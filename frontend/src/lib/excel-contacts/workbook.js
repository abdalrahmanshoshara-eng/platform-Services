import ExcelJS from "exceljs";
import JSZip from "jszip";
import * as XLSX from "xlsx";
import {
  EXPECTED_COLUMNS,
  createVcard,
  normalizeHeader,
  processContactRows,
} from "./contacts";

const REPORT_COLUMNS = {
  valid: ["الاسم الكامل", "رقم التواصل", "البريد الالكتروني"],
  duplicate: [
    "صف Excel المكرر",
    "الاسم الكامل المكرر",
    "رقم التواصل",
    "البريد الالكتروني المكرر",
    "صف Excel المحتفظ به",
    "الاسم المحتفظ به",
    "ملاحظة",
  ],
  invalid: [
    "صف Excel",
    "الاسم الكامل",
    "رقم التواصل الأصلي",
    "البريد الالكتروني الأصلي",
    "سبب الاستبعاد",
  ],
};

export function parseExcelFile(buffer) {
  const workbook = XLSX.read(buffer, {
    type: "buffer",
    cellDates: false,
    dense: false,
  });

  if (!workbook.SheetNames.length) {
    throw new Error("ملف Excel لا يحتوي على أوراق عمل.");
  }

  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const matrix = XLSX.utils.sheet_to_json(sheet, {
    header: 1,
    defval: "",
    raw: true,
    blankrows: false,
  });

  if (matrix.length === 0) {
    throw new Error("ورقة العمل الأولى فارغة.");
  }

  const headers = matrix[0].map(normalizeHeader);
  const missingColumns = EXPECTED_COLUMNS.filter(
    (column) => !headers.includes(column),
  );

  if (missingColumns.length > 0) {
    throw new Error(
      `الأعمدة التالية غير موجودة: ${missingColumns.join("، ")}. ` +
        `الأعمدة الموجودة: ${headers.filter(Boolean).join("، ") || "لا يوجد"}`,
    );
  }

  const indexByHeader = new Map(headers.map((header, index) => [header, index]));
  const rows = matrix.slice(1).map((cells) => {
    const row = {};
    for (const column of EXPECTED_COLUMNS) {
      row[column] = cells[indexByHeader.get(column)] ?? "";
    }
    return row;
  });

  return { rows, sheetName };
}

function calculateWidth(columnName, rows) {
  const longest = rows.reduce((max, row) => {
    return Math.max(max, String(row[columnName] ?? "").length);
  }, columnName.length);
  return Math.min(Math.max(longest + 3, 14), 48);
}

async function createExcelReport({ sheetName, columns, rows, headerColor }) {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = "WhatsApp Contacts Web";
  workbook.created = new Date();

  const worksheet = workbook.addWorksheet(sheetName, {
    views: [{ state: "frozen", ySplit: 1, rightToLeft: true }],
  });

  worksheet.columns = columns.map((column) => ({
    header: column,
    key: column,
    width: calculateWidth(column, rows),
  }));

  rows.forEach((row) => worksheet.addRow(row));
  worksheet.autoFilter = {
    from: { row: 1, column: 1 },
    to: { row: 1, column: columns.length },
  };

  const headerRow = worksheet.getRow(1);
  headerRow.height = 25;
  headerRow.eachCell((cell) => {
    cell.font = { bold: true, color: { argb: "FF1F2937" } };
    cell.fill = {
      type: "pattern",
      pattern: "solid",
      fgColor: { argb: headerColor },
    };
    cell.alignment = { horizontal: "center", vertical: "middle" };
    cell.border = {
      bottom: { style: "thin", color: { argb: "FFCBD5E1" } },
    };
  });

  worksheet.eachRow((row, rowNumber) => {
    if (rowNumber === 1) return;
    row.alignment = { vertical: "middle", horizontal: "right" };
    if (rowNumber % 2 === 0) {
      row.eachCell((cell) => {
        cell.fill = {
          type: "pattern",
          pattern: "solid",
          fgColor: { argb: "FFF8FAFC" },
        };
      });
    }
  });

  return Buffer.from(await workbook.xlsx.writeBuffer());
}

function makeSummaryText({ sourceFileName, sourceSheetName, countryCode, summary }) {
  const createdAt = new Intl.DateTimeFormat("ar-SY", {
    dateStyle: "full",
    timeStyle: "medium",
    timeZone: "UTC",
  }).format(new Date());

  return [
    "تقرير تحويل جهات الاتصال",
    `تاريخ الإنشاء (UTC): ${createdAt}`,
    `الملف المصدر: ${sourceFileName}`,
    `ورقة العمل المستخدمة: ${sourceSheetName}`,
    `إجمالي الصفوف: ${summary.totalRows}`,
    `جهات الاتصال الفريدة المقبولة: ${summary.validCount}`,
    `السجلات المكررة التي تم دمجها: ${summary.duplicateCount}`,
    `الصفوف الخاطئة التي تحتاج مراجعة: ${summary.invalidCount}`,
    "طريقة إزالة التكرار: الاحتفاظ بأول ظهور لكل رقم تواصل بعد توحيد صيغته",
    `رمز الدولة الافتراضي للأرقام المحلية: +${countryCode}`,
    "",
  ].join("\n");
}

export async function processExcelAndBuildArchive({
  buffer,
  sourceFileName,
  countryCode,
}) {
  const { rows, sheetName } = parseExcelFile(buffer);

  if (rows.length > 10000) {
    throw new Error("الحد الأعلى المدعوم هو 10,000 صف لكل ملف.");
  }

  const result = processContactRows(rows, countryCode);
  const zip = new JSZip();

  zip.file("contacts.vcf", createVcard(result.validRows));
  zip.file(
    "clean_contacts.xlsx",
    await createExcelReport({
      sheetName: "جهات الاتصال الفريدة",
      columns: REPORT_COLUMNS.valid,
      rows: result.validRows,
      headerColor: "FFD9EAD3",
    }),
  );
  zip.file(
    "merged_duplicates.xlsx",
    await createExcelReport({
      sheetName: "مكررات تم دمجها",
      columns: REPORT_COLUMNS.duplicate,
      rows: result.duplicateRows,
      headerColor: "FFFCE5CD",
    }),
  );
  zip.file(
    "invalid_rows.xlsx",
    await createExcelReport({
      sheetName: "صفوف تحتاج مراجعة",
      columns: REPORT_COLUMNS.invalid,
      rows: result.invalidRows,
      headerColor: "FFF4CCCC",
    }),
  );
  zip.file(
    "summary.txt",
    makeSummaryText({
      sourceFileName,
      sourceSheetName: sheetName,
      countryCode,
      summary: result.summary,
    }),
  );

  const zipBuffer = await zip.generateAsync({
    type: "nodebuffer",
    compression: "DEFLATE",
    compressionOptions: { level: 6 },
  });

  return {
    ...result,
    zipBuffer,
    sourceSheetName: sheetName,
  };
}
