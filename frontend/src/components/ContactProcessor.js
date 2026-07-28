"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  excelContactsErrorMessage,
  processExcelContacts,
} from "@/features/excel-contacts/api";

const REQUIRED_COLUMNS = [
  "الاسم الكامل",
  "رقم التواصل",
  "البريد الالكتروني",
];

const TABS = [
  { id: "valid", label: "المقبولة", countKey: "validCount" },
  { id: "duplicate", label: "المكررة", countKey: "duplicateCount" },
  { id: "invalid", label: "تحتاج مراجعة", countKey: "invalidCount" },
];

function formatFileSize(bytes) {
  if (!bytes) return "0 KB";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function base64ToBlob(base64) {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: "application/zip" });
}

function PreviewTable({ rows }) {
  const columns = useMemo(() => {
    if (!rows?.length) return [];
    return Object.keys(rows[0]);
  }, [rows]);

  if (!rows?.length) {
    return <div className="empty-state">لا توجد سجلات ضمن هذه الفئة.</div>;
  }

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`${rowIndex}-${Object.values(row).join("-")}`}>
              {columns.map((column) => (
                <td key={column}>{String(row[column] ?? "") || "—"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ContactProcessor() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [countryCode, setCountryCode] = useState("963");
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState("");
  const [activeTab, setActiveTab] = useState("valid");

  useEffect(() => {
    return () => {
      if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    };
  }, [downloadUrl]);

  function chooseFile(selectedFile) {
    if (!selectedFile) return;
    const lowerName = selectedFile.name.toLowerCase();
    if (!lowerName.endsWith(".xlsx") && !lowerName.endsWith(".xls")) {
      setError("اختر ملفًا بصيغة .xlsx أو .xls.");
      return;
    }
    setError("");
    setResult(null);
    setFile(selectedFile);
  }

  function reset() {
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    setDownloadUrl("");
    setFile(null);
    setResult(null);
    setError("");
    setActiveTab("valid");
    if (inputRef.current) inputRef.current.value = "";
  }

  async function processFile() {
    if (!file) {
      setError("اختر ملف Excel أولًا.");
      return;
    }

    setIsProcessing(true);
    setError("");

    try {
      const payload = await processExcelContacts(file, countryCode);

      if (downloadUrl) URL.revokeObjectURL(downloadUrl);
      const url = URL.createObjectURL(base64ToBlob(payload.zipBase64));
      setDownloadUrl(url);
      setResult(payload);
      setActiveTab("valid");
    } catch (processingError) {
      setError(excelContactsErrorMessage(processingError));
      setResult(null);
    } finally {
      setIsProcessing(false);
    }
  }

  return (
    <section className="workspace-card excel-workspace">
      <div className="steps-row" aria-label="خطوات الاستخدام">
        <span className="step active"><b>1</b> رفع الملف</span>
        <span className="step"><b>2</b> المراجعة</span>
        <span className="step"><b>3</b> تنزيل النتائج</span>
      </div>

      <div className="form-grid">
        <div>
          <label className="field-label">ملف Excel</label>
          <button
            type="button"
            className={`drop-zone ${isDragging ? "dragging" : ""}`}
            onClick={() => inputRef.current?.click()}
            onDragEnter={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragging(false);
              chooseFile(event.dataTransfer.files?.[0]);
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.xls"
              hidden
              onChange={(event) => chooseFile(event.target.files?.[0])}
            />
            <span className="upload-icon" aria-hidden="true">↑</span>
            {file ? (
              <>
                <strong>{file.name}</strong>
                <span>{formatFileSize(file.size)}</span>
              </>
            ) : (
              <>
                <strong>اسحب ملف Excel هنا</strong>
                <span>أو اضغط لاختيار الملف — الحد الأعلى 10 MB</span>
              </>
            )}
          </button>
        </div>

        <div className="settings-panel">
          <label className="field-label" htmlFor="country-code">
            رمز الدولة الافتراضي
          </label>
          <div className="country-field">
            <span>+</span>
            <input
              id="country-code"
              inputMode="numeric"
              value={countryCode}
              maxLength={4}
              onChange={(event) =>
                setCountryCode(event.target.value.replace(/\D/g, ""))
              }
            />
          </div>
          <p className="field-help">
            يُستخدم فقط للأرقام المحلية التي تبدأ بصفر. سوريا: 963.
          </p>

          <a className="template-link" href="/contact-template.xlsx" download>
            تنزيل قالب Excel جاهز
          </a>
        </div>
      </div>

      <div className="required-columns">
        <span>الأعمدة المطلوبة:</span>
        {REQUIRED_COLUMNS.map((column) => (
          <code key={column}>{column}</code>
        ))}
      </div>

      {error && <div className="alert error-alert">{error}</div>}

      <div className="action-row">
        <button
          className="primary-button"
          type="button"
          disabled={!file || isProcessing || !countryCode}
          onClick={processFile}
        >
          {isProcessing ? <span className="spinner" /> : null}
          {isProcessing ? "جارٍ تجهيز النتائج..." : "معالجة الملف"}
        </button>
        {(file || result) && (
          <button className="secondary-button" type="button" onClick={reset}>
            البدء من جديد
          </button>
        )}
      </div>

      {result && (
        <div className="results-section">
          <div className="results-heading">
            <div>
              <p className="eyebrow">اكتملت المعالجة</p>
              <h2>نتيجة الملف</h2>
              <p>تم استخدام ورقة العمل: {result.sourceSheetName}</p>
            </div>
            <a
              className="download-button"
              href={downloadUrl}
              download={result.fileName}
            >
              تنزيل ملف ZIP
            </a>
          </div>

          <div className="stats-grid">
            <article><span>إجمالي الصفوف</span><strong>{result.summary.totalRows}</strong></article>
            <article className="success"><span>جهات فريدة</span><strong>{result.summary.validCount}</strong></article>
            <article className="warning"><span>مكررات مدمجة</span><strong>{result.summary.duplicateCount}</strong></article>
            <article className="danger"><span>تحتاج مراجعة</span><strong>{result.summary.invalidCount}</strong></article>
          </div>

          <div className="tabs" role="tablist">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                className={activeTab === tab.id ? "selected" : ""}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
                <span>{result.summary[tab.countKey]}</span>
              </button>
            ))}
          </div>

          <PreviewTable rows={result.previews[activeTab]} />
          <p className="preview-note">تعرض الواجهة أول 10 سجلات فقط. التقارير الكاملة موجودة داخل ZIP.</p>

          <div className="zip-list">
            <strong>محتويات الحزمة:</strong>
            <span>contacts.vcf</span>
            <span>clean_contacts.xlsx</span>
            <span>merged_duplicates.xlsx</span>
            <span>invalid_rows.xlsx</span>
            <span>summary.txt</span>
          </div>
        </div>
      )}
    </section>
  );
}
