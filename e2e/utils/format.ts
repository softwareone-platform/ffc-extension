const padTo2Digits = (num: number): string => num.toString().padStart(2, '0');

export function limitString(input: string, maxLength: number): string {
  return input.length > maxLength ? `${input.substring(0, maxLength)}...` : input;
}

export function formatDateToYmdHms(date: Date): string {
  const ymd = [date.getFullYear(), padTo2Digits(date.getMonth() + 1), padTo2Digits(date.getDate())].join('-');
  const hms = [padTo2Digits(date.getHours()), padTo2Digits(date.getMinutes()), padTo2Digits(date.getSeconds())].join(':');
  return `${ymd} ${hms}`;
}
