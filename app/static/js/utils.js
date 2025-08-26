// format a date into dd-mm-yyyy hh:mm:ss
export function formatDate(date) {
  const dd = String(date.getDate()).padStart(2, "0");
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const yyyy = date.getFullYear();
  const hh = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  const ss = String(date.getSeconds()).padStart(2, "0");
  return `${dd}-${mm}-${yyyy} ${hh}:${min}:${ss}`;
}

// get the current date & time
export function getCurrentDateTime() {
  const now = new Date();
  return `${String(now.getDate()).padStart(2, "0")}.${String(
    now.getMonth() + 1
  ).padStart(2, "0")}.${now.getFullYear()}, ${String(now.getHours()).padStart(
    2,
    "0"
  )}:${String(now.getMinutes()).padStart(2, "0")}:${String(
    now.getSeconds()
  ).padStart(2, "0")}`;
}
