// format a Date object into dd-mm-yyyy hh:mm:ss
export function formatDate(date, dateSeparator = ".", timeSeparator = ":") {
  const dd = String(date.getDate()).padStart(2, "0");
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const yyyy = date.getFullYear();
  const hh = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  const ss = String(date.getSeconds()).padStart(2, "0");

  return `${dd}${dateSeparator}${mm}${dateSeparator}${yyyy} ${hh}${timeSeparator}${min}${timeSeparator}${ss}`;
}

// get current datetime (just a wrapper)
export function getCurrentDateTime() {
  return formatDate(new Date(), ".", ":");
}

// convert all elements with class .timestamp from UTC to local
export function localizeTimestamps() {
  document.querySelectorAll(".timestamp").forEach((el) => {
    const utc = el.dataset.utc;
    if (!utc) return;

    const localDate = new Date(utc.trim());
    if (isNaN(localDate)) return;

    el.textContent = formatDate(localDate, ".", ":");
  });
}

export function localizeTimestamp(ts) {
  const localDate = new Date(ts);
  if (isNaN(localDate)) return;

  return formatDate(localDate, ".", ":");
}
