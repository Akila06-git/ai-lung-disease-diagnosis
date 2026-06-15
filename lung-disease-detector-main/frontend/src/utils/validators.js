export const ACCEPTED_TYPES = ["image/jpeg", "image/jpg", "image/png", "application/dicom", ""];
export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

export const isImageFile = (file) => {
  if (ACCEPTED_TYPES.includes(file.type)) return true;
  return file.name.toLowerCase().endsWith(".dcm") || file.name.toLowerCase().endsWith(".dicom");
};

export const isWithinSizeLimit = (file) => file.size <= MAX_FILE_SIZE_BYTES;

export const formatFileSize = (bytes) => {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${bytes} B`;
};

export const getImageDimensions = (file) =>
  new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve({ width: img.width, height: img.height });
    img.onerror = () => reject(new Error("Could not read image dimensions"));
    img.src = URL.createObjectURL(file);
  });

