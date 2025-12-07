/**
 * Hàm làm tròn số 2 số sau thập phân
 * @params num
 * @return {số thập phân sau khi xử lý}
 */
const roundToTwo = (num: number): number => {
  if (typeof num !== 'number') return num;
  return parseFloat(num.toFixed(2));
};

/**
 * Hàm chuẩn hóa Date thành "dd/MM/yyyy"
 * @param date
 * @returns {định dạng ngày sau khi xử lý}
 */
const formatDate = (date: string): string => {
  const newdate = new Date(date);

  const day = newdate.getDate().toString().padStart(2, '0');
  const month = (newdate.getMonth() + 1).toString().padStart(2, '0');
  const year = newdate.getFullYear();
  const hours = newdate.getHours().toString().padStart(2, '0');
  const minutes = newdate.getMinutes().toString().padStart(2, '0');

  return `${day}/${month}/${year} ${hours}:${minutes}`;
};

export {formatDate, roundToTwo}