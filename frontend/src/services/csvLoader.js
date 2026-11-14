import Papa from 'papaparse';

/**
 * Loads and parses a CSV file from the public directory.
 * @param {string} filename Name of the file inside /data/
 * @returns {Promise<Array>} Array of parsed objects
 */
export const loadCSV = (filename) => {
  return new Promise((resolve, reject) => {
    Papa.parse(`/data/${filename}`, {
      download: true,
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
      complete: (results) => {
        resolve(results.data);
      },
      error: (error) => {
        console.error(`Error loading CSV ${filename}:`, error);
        reject(error);
      },
    });
  });
};

/**
 * Parses raw CSV string or file content (used for upload validation).
 * @param {string|File} file CSV file or text
 * @returns {Promise<Array>}
 */
export const parseRawCSV = (file) => {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
      complete: (results) => {
        resolve(results.data);
      },
      error: (err) => reject(err),
    });
  });
};

