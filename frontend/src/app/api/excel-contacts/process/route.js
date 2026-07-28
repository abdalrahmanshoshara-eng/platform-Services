import { normalizeCountryCode } from "@/lib/excel-contacts/contacts";
import { processExcelAndBuildArchive } from "@/lib/excel-contacts/workbook";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".xlsx", ".xls"];

function getExtension(fileName) {
  const index = fileName.lastIndexOf(".");
  return index === -1 ? "" : fileName.slice(index).toLowerCase();
}

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    const countryCode = normalizeCountryCode(formData.get("countryCode") || "963");

    if (!file || typeof file.arrayBuffer !== "function") {
      return Response.json(
        { error: "اختر ملف Excel أولًا." },
        { status: 400 },
      );
    }

    const extension = getExtension(file.name || "");
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return Response.json(
        { error: "الصيغ المدعومة هي .xlsx و .xls فقط." },
        { status: 400 },
      );
    }

    if (file.size === 0) {
      return Response.json({ error: "الملف المرفوع فارغ." }, { status: 400 });
    }

    if (file.size > MAX_FILE_SIZE) {
      return Response.json(
        { error: "حجم الملف أكبر من الحد المسموح وهو 10 ميغابايت." },
        { status: 413 },
      );
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    const result = await processExcelAndBuildArchive({
      buffer,
      sourceFileName: file.name,
      countryCode,
    });

    const timestamp = new Date().toISOString().replaceAll(":", "-").slice(0, 19);

    return Response.json(
      {
        fileName: `contacts-output-${timestamp}.zip`,
        zipBase64: result.zipBuffer.toString("base64"),
        summary: result.summary,
        sourceSheetName: result.sourceSheetName,
        previews: {
          valid: result.validRows.slice(0, 10),
          duplicate: result.duplicateRows.slice(0, 10),
          invalid: result.invalidRows.slice(0, 10),
        },
      },
      {
        status: 200,
        headers: { "Cache-Control": "no-store" },
      },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "حدث خطأ غير متوقع أثناء المعالجة.";

    return Response.json(
      { error: message },
      {
        status: 400,
        headers: { "Cache-Control": "no-store" },
      },
    );
  }
}
