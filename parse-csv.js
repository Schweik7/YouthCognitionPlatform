import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// ES模块中获取__dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// CSV文件路径
const practiceTrialPath = path.join(__dirname, 'server', '教学阶段.csv');
const formalTrialPath = path.join(__dirname, 'server', '正式阶段.csv');

// 解析CSV函数
function parseCSV(filePath) {
  try {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const records = parse(fileContent);
    
    // 处理每条记录，提取句子内容
    return records.map(record => {
      // 假设每条记录的第二个字段是句子内容
      // 如果CSV格式不同，请调整此处逻辑
      return record[1] || record[0];
    });
  } catch (error) {
    console.error(`解析CSV文件失败: ${filePath}`, error);
    return [];
  }
}

// 解析练习阶段CSV
const practiceTrials = parseCSV(practiceTrialPath);
console.log('练习阶段题目:');
console.log(practiceTrials);

// 解析正式阶段CSV
const formalTrials = parseCSV(formalTrialPath);
console.log(`正式阶段题目数量: ${formalTrials.length}`);
console.log('前5个正式题目样例:');
console.log(formalTrials.slice(0, 5));

// 导出解析结果
export { practiceTrials, formalTrials };