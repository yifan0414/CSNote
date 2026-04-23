<%*
let list = {
  "ℹ️ info" : "info,資訊",
  "✏️ note" : "note,筆記",
  "📒 summary" : "summary,彙總",
  "🔥 tip" : "tip,技巧",
  "☑️ check" : "check,查核",
  "❔Help" : "help,說明",
  "⚠️ Warning" : "warning,警告",
  "❌ Fail" : "fail,失敗",
  "⚡Danger" : "danger,危險",
  "🪲 Bug" : "bug,錯誤",
  "📋 Example" : "example,範例",
  "✍️ Quote " : "quote,引用",
  "😝 LOL " : "LOL,哈哈",
  "📕 Reference " : "REF,參考"
};
let keys = Object.keys(list);
key = await tp.system.suggester(keys, keys);
let value = list[key];
let index = value.indexOf(",");
let text = value.substring(index+1);
value = value.substring(0, index);
if (key) return ">[!" + value + "]+ " + text + "\n> ";
%>