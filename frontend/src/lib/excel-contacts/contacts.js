const ARABIC_DIGIT_TRANSLATION = new Map([
  ["٠", "0"], ["١", "1"], ["٢", "2"], ["٣", "3"], ["٤", "4"],
  ["٥", "5"], ["٦", "6"], ["٧", "7"], ["٨", "8"], ["٩", "9"],
  ["۰", "0"], ["۱", "1"], ["۲", "2"], ["۳", "3"], ["۴", "4"],
  ["۵", "5"], ["۶", "6"], ["۷", "7"], ["۸", "8"], ["۹", "9"],
]);

export const EXPECTED_COLUMNS = [
  "الاسم الكامل",
  "رقم التواصل",
  "البريد الالكتروني",
];

export function isEmpty(value) {
  return value === null || value === undefined || String(value).trim() === "";
}

export function normalizeHeader(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .replace(/^\uFEFF/, "")
    .trim()
    .replace(/\s+/g, " ");
}

export function valueToText(value) {
  if (isEmpty(value)) return "";

  if (typeof value === "number") {
    if (!Number.isFinite(value)) return "";
    if (Number.isInteger(value)) return String(value);
    return value.toFixed(12).replace(/0+$/, "").replace(/\.$/, "");
  }

  const text = String(value).trim();
  if (/^[+-]?\d+(?:\.\d+)?e[+-]?\d+$/i.test(text)) {
    const numeric = Number(text);
    if (Number.isFinite(numeric)) {
      return numeric.toLocaleString("en-US", {
        useGrouping: false,
        maximumFractionDigits: 20,
      });
    }
  }

  return text.replace(/\.0+$/, "");
}

export function cleanPhoneText(value) {
  let text = valueToText(value)
    .normalize("NFKC")
    .replace(/[٠-٩۰-۹]/g, (digit) => ARABIC_DIGIT_TRANSLATION.get(digit))
    .trim()
    .replace(/[^0-9+]/g, "");

  if (text.includes("+")) {
    text = `${text.startsWith("+") ? "+" : ""}${text.replaceAll("+", "")}`;
  }

  if (text.startsWith("00")) {
    text = `+${text.slice(2)}`;
  }

  return text;
}

export function normalizeCountryCode(value) {
  const code = String(value ?? "").replace(/\D/g, "");
  if (!/^\d{1,4}$/.test(code)) {
    throw new Error("رمز الدولة يجب أن يتكون من 1 إلى 4 أرقام.");
  }
  return code;
}

export function normalizePhone(value, countryCode = "963") {
  const defaultCountryCode = normalizeCountryCode(countryCode);
  const raw = cleanPhoneText(value);

  if (!raw) throw new Error("رقم التواصل فارغ");

  if (raw.startsWith("+")) {
    const digits = raw.slice(1);
    if (!/^\d{8,15}$/.test(digits)) {
      throw new Error(`رقم دولي غير صالح: ${raw}`);
    }
    return `+${digits}`;
  }

  if (!/^\d+$/.test(raw)) {
    throw new Error(`تعذر فهم الرقم: ${raw}`);
  }

  if (raw.startsWith(defaultCountryCode)) {
    if (raw.length < 8 || raw.length > 15) {
      throw new Error(`رقم غير صالح: ${raw}`);
    }
    return `+${raw}`;
  }

  if (raw.startsWith("0")) {
    const local = raw.slice(1);
    if (local.length < 7 || local.length > 12) {
      throw new Error(`رقم محلي غير صالح: ${raw}`);
    }
    return `+${defaultCountryCode}${local}`;
  }

  if (defaultCountryCode === "963" && /^9\d{8}$/.test(raw)) {
    return `+${defaultCountryCode}${raw}`;
  }

  throw new Error(
    `رقم غير معروف الصيغة: ${raw}. استخدم صيغة دولية مثل +${defaultCountryCode}9XXXXXXXX`,
  );
}

export function cleanEmail(value) {
  if (isEmpty(value)) return "";

  const email = String(value).normalize("NFKC").trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    throw new Error("بريد إلكتروني غير صالح");
  }
  return email;
}

export function escapeVcard(value) {
  return String(value)
    .replaceAll("\\", "\\\\")
    .replaceAll("\r\n", "\\n")
    .replaceAll("\n", "\\n")
    .replaceAll(";", "\\;")
    .replaceAll(",", "\\,");
}

export function createVcard(contacts, category = "WhatsApp Excel Import") {
  const lines = [];

  for (const contact of contacts) {
    const name = escapeVcard(contact["الاسم الكامل"]);
    const phone = contact["رقم التواصل"];
    const email = escapeVcard(contact["البريد الالكتروني"] ?? "");

    lines.push(
      "BEGIN:VCARD",
      "VERSION:3.0",
      `FN;CHARSET=UTF-8:${name}`,
      `N;CHARSET=UTF-8:;${name};;;`,
      `TEL;TYPE=CELL:${phone}`,
    );

    if (email) lines.push(`EMAIL;TYPE=INTERNET:${email}`);
    lines.push(`CATEGORIES:${category}`, "END:VCARD");
  }

  return `${lines.join("\r\n")}\r\n`;
}

export function processContactRows(rows, countryCode = "963") {
  const validRows = [];
  const invalidRows = [];
  const duplicateRows = [];
  const seenPhones = new Map();

  rows.forEach((row, index) => {
    const excelRow = index + 2;
    const name = isEmpty(row["الاسم الكامل"])
      ? ""
      : String(row["الاسم الكامل"]).trim();
    const rawPhone = row["رقم التواصل"];
    const rawEmail = row["البريد الالكتروني"];

    const reasons = [];
    let normalizedPhone = "";
    let normalizedEmail = "";

    if (!name) reasons.push("الاسم الكامل فارغ");

    try {
      normalizedPhone = normalizePhone(rawPhone, countryCode);
    } catch (error) {
      reasons.push(error.message);
    }

    try {
      normalizedEmail = cleanEmail(rawEmail);
    } catch (error) {
      reasons.push(error.message);
    }

    if (reasons.length > 0) {
      invalidRows.push({
        "صف Excel": excelRow,
        "الاسم الكامل": name,
        "رقم التواصل الأصلي": valueToText(rawPhone),
        "البريد الالكتروني الأصلي": isEmpty(rawEmail)
          ? ""
          : String(rawEmail).trim(),
        "سبب الاستبعاد": reasons.join(" | "),
      });
      return;
    }

    if (seenPhones.has(normalizedPhone)) {
      const firstRecord = seenPhones.get(normalizedPhone);
      duplicateRows.push({
        "صف Excel المكرر": excelRow,
        "الاسم الكامل المكرر": name,
        "رقم التواصل": normalizedPhone,
        "البريد الالكتروني المكرر": normalizedEmail,
        "صف Excel المحتفظ به": firstRecord.excelRow,
        "الاسم المحتفظ به": firstRecord.name,
        "ملاحظة": "تم الاحتفاظ بأول ظهور وتجاهل هذا التكرار",
      });
      return;
    }

    seenPhones.set(normalizedPhone, { excelRow, name });
    validRows.push({
      "الاسم الكامل": name,
      "رقم التواصل": normalizedPhone,
      "البريد الالكتروني": normalizedEmail,
    });
  });

  return {
    validRows,
    duplicateRows,
    invalidRows,
    summary: {
      totalRows: rows.length,
      validCount: validRows.length,
      duplicateCount: duplicateRows.length,
      invalidCount: invalidRows.length,
    },
  };
}
