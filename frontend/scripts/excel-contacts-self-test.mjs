import assert from "node:assert/strict";
import { normalizePhone, processContactRows } from "../src/lib/excel-contacts/contacts.js";

assert.equal(normalizePhone("0933123456", "963"), "+963933123456");
assert.equal(normalizePhone("933123456", "963"), "+963933123456");
assert.equal(normalizePhone("00963933123456", "963"), "+963933123456");
assert.equal(normalizePhone("+963 933 123 456", "963"), "+963933123456");
assert.equal(normalizePhone("٠٩٣٣١٢٣٤٥٦", "963"), "+963933123456");

const result = processContactRows([
  {
    "الاسم الكامل": "أحمد الأول",
    "رقم التواصل": "0933123456",
    "البريد الالكتروني": "first@example.com",
  },
  {
    "الاسم الكامل": "أحمد المكرر",
    "رقم التواصل": "+963933123456",
    "البريد الالكتروني": "second@example.com",
  },
  {
    "الاسم الكامل": "ليلى",
    "رقم التواصل": "0944123456",
    "البريد الالكتروني": "invalid-email",
  },
]);

assert.equal(result.summary.totalRows, 3);
assert.equal(result.summary.validCount, 1);
assert.equal(result.summary.duplicateCount, 1);
assert.equal(result.summary.invalidCount, 1);
assert.equal(result.validRows[0]["الاسم الكامل"], "أحمد الأول");

console.log("Self-test passed.");
