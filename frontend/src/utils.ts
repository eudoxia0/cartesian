const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
];

export function humanizeDate(createdAt: number): string {
    const stamp = new Date(createdAt);
    const [year, month, day] = [stamp.getFullYear(), monthNames[stamp.getMonth()], stamp.getDate()];
    const [hours, minutes, seconds] = [stamp.getHours(), stamp.getMinutes(), stamp.getSeconds()];
    const tz = -(stamp.getTimezoneOffset() / 60);
    return `${month} ${day}, ${year} at ${hours}:${minutes}:${seconds} UTC+${tz}`;
}

export function humanizeFileSize(size: number): string {
    size = Math.abs(size);
    let unitIdx = 0;
    const radix = 1024;
    while (size >= radix) {
        size /= radix;
        ++unitIdx;
    }
    const units = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB'];
    return `${size.toFixed(2)} ${units[unitIdx]}`;
}