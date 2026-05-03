import * as XLSX from "xlsx";

export function xlsxBufferToCsv(buffer: Buffer): string {
  const wb = XLSX.read(buffer, { type: "buffer" });
  const name = wb.SheetNames[0];
  if (!name) return "";
  const sheet = wb.Sheets[name];
  return XLSX.utils.sheet_to_csv(sheet, { FS: ",", RS: "\n" });
}
