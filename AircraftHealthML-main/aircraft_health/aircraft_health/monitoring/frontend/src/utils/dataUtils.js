export const loadProcessedData = async (filename) => {
    const response = await fetch(`../../../ml_models/data/ADAPT/processed/${filename}`);
    const text = await response.text();
    return text;
  };
  
  export const parseCSV = (text) => {
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',');
    return lines.slice(1).map(line => {
      const values = line.split(',');
      const obj = {};
      headers.forEach((header, i) => {
        obj[header] = values[i];
      });
      return obj;
    });
  };