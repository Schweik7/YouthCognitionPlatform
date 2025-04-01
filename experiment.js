import { initJsPsych } from 'jspsych';
import htmlKeyboardResponse from '@jspsych/plugin-html-keyboard-response';

// 初始化jsPsych
const jsPsych = initJsPsych({
  display_element: 'jspsych-target'
});

// 定义实验试验
const trial = {
  type: htmlKeyboardResponse,
  stimulus: 'Hello world!'
};

// 运行实验
jsPsych.run([trial]);