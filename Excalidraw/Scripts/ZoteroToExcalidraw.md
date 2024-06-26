let settings = ea.getScriptSettings();
//set default values on first run
if (!settings["Zotero Library Path"]) settings["Zotero Library Path"] = { value: false };
if (!settings["Zotero Library Path"].value) {
	new Notice("🔴请配置Zotero的Library路径和其他相关设置！", 2000);
	settings = {
		"Zotero Library Path": {
			value: "",
			description: "Zotero Library的路径，比如：D:/Zotero/cache/library"
		},
		"Zotero Images Path": {
			value: "./",
			description: "Obsidian库内存放Zotero的图片的相对路径，比如：Y-图形文件存储/ZoteroImages"
		},
		"Zotero Annotations Color": {
			value: false,
			description: "是否开启匹配Zotero的颜色选项栏<br>❗注：匹配颜色选项需要修改Zotero的高亮标注模板",
		},
	};
	ea.setScriptSettings(settings);
} else {
	new Notice("✅ZoteroToExcalidraw脚本已启动！");
}

const path = require('path');
const fs = require("fs");

// 获取库的基本路径
const basePath = (app.vault.adapter).getBasePath();
// 📌修改到Zotero的library文件夹
const zotero_library_path = settings["Zotero Library Path"].value;
// 设置相对路径
const relativePath = settings["Zotero Images Path"].value;

// let api = ea.getExcalidrawAPI();
let el = ea.targetView.containerEl.querySelectorAll(".excalidraw-wrapper")[0];

let InsertStyle;
if (settings["Zotero Annotations Color"].value) {
	const fillStyles = ["文字", "背景"];
	InsertStyle = await utils.suggester(fillStyles, fillStyles, "选择插入卡片颜色的形式，ESC则为白底黑字)");
}

el.ondrop = async function (event) {
	console.log("ondrop");
	event.preventDefault();
	var insert_txt = event.dataTransfer.getData("Text");
	const ondropType = event.dataTransfer.files.length;
	console.log(ondropType);

	// 设定一些样式
	ea.style.strokeStyle = "solid";
	ea.style.fillStyle = 'solid';
	ea.style.roughness = 0;
	ea.style.backgroundColor = "transparent";
	ea.style.strokeColor = "#1e1e1e";
	// ea.style.roundness = { type: 3 }; // 圆角
	ea.style.strokeWidth = 2;
	ea.style.fontFamily = 4;
	ea.style.fontSize = 20;

	if (insert_txt.includes("zotero://")) {
		// 格式化文本(去空格、全角转半角)  
		insert_txt = processText(insert_txt);
		// 清空原本投入的文本
		event.stopPropagation();
		ea.clear();
		console.log("Zotero");

		let zotero_color = match_zotero_color(insert_txt);
		// alert(zotero_color);

		if (zotero_color) {
			// 卡片背景颜色
			if (InsertStyle == "背景") {
				ea.style.backgroundColor = zotero_color;
				ea.style.strokeColor = "#1e1e1e";
			} else if (InsertStyle == "文字") {
				ea.style.backgroundColor = "#ffffff";
				ea.style.strokeColor = zotero_color;
			} else {
				ea.style.backgroundColor = "transparent";
				ea.style.strokeColor = "#1e1e1e";
			}
		} else {
			ea.style.backgroundColor = "transparent";
			ea.style.strokeColor = "#1e1e1e";
		}

		zotero_txt = match_zotero_txt(insert_txt);
		zotero_author = match_zotero_author(insert_txt);
		if (zotero_author) {
			zotero_author = `\n(${zotero_author})`;
		};
		zotero_comment = match_zotero_comment(insert_txt);
		if (zotero_comment) {
			zotero_comment = `\n\n📝：${zotero_comment}`;
		};
		zotero_link = match_zotero_link(insert_txt);

		if (zotero_txt) {
			console.log("ZoteroText");

			let id = await ea.addText(0, 0, `📖：${zotero_txt}${zotero_author}${zotero_comment}`, { width: 600, box: true, wrapAt: 90, textAlign: "left", textVerticalAlign: "middle", box: "box" });
			let el = ea.getElement(id);
			el.link = zotero_link;
			await ea.addElementsToView(true, true, false);
			if (ea.targetView.draginfoDiv) {
				document.body.removeChild(ea.targetView.draginfoDiv);
				delete ea.targetView.draginfoDiv;
			};
		} else {
			console.log("ZoteroImage");
			let zotero_image = match_zotero_image(insert_txt);
			let zotero_image_name = `${zotero_image}.png`;
			let Obsidian_image_Path = `${basePath}/${relativePath}/${zotero_image_name}`;

			// 如果Ob的路径不存在则创建
			if (!fs.existsSync(`${basePath}/${relativePath}`)) {
				fs.mkdirSync(path.dirname(`${basePath}/${relativePath}`), { recursive: true });
			}
			let zotero_image_path = `${zotero_library_path}/${zotero_image_name}`;

			// 复制zotero的图片到Obsidian的笔记库
			fs.copyFileSync(zotero_image_path, Obsidian_image_Path);
			await new Promise((resolve) => setTimeout(resolve, 200)); // 暂停0.2秒，等待复制文件的过程

			let id = await ea.addImage(0, 0, zotero_image_name);
			let el = ea.getElement(id);
			el.link = zotero_link;

			await ea.addElementsToView(true, true, false);
			if (ea.targetView.draginfoDiv) {
				document.body.removeChild(ea.targetView.draginfoDiv);
				delete ea.targetView.draginfoDiv;
			};
		};

	} else if (ondropType < 1) {
		// 清空原本投入的文本
		event.stopPropagation();
		ea.clear();
		// 格式化文本(去空格、全角转半角)  
		insert_txt = processText(insert_txt);
		console.log("文本格式化");
		await ea.addText(0, 0, `${insert_txt} `, { width: 400, box: true, wrapAt: 90, textAlign: "left", textVerticalAlign: "middle", box: "box" });
		// let el = ea.getElement(id);
		await ea.addElementsToView(true, true, false);
		if (ea.targetView.draginfoDiv) {
			document.body.removeChild(ea.targetView.draginfoDiv);
			delete ea.targetView.draginfoDiv;
		};
	};
};

function processText(text) {
	// 替换特殊空格为普通空格
	text = text.replace(/[\ue5d2\u00a0\u2007\u202F\u3000\u314F\u316D\ue5cf]/g, ' ');
	// 将全角字符转换为半角字符
	text = text.replace(/[\uFF01-\uFF5E]/g, function (match) { return String.fromCharCode(match.charCodeAt(0) - 65248); });
	// 替换英文之间的多个空格为一个空格
	text = text.replace(/([a-zA-Z])([\u4e00-\u9fa5])/g, '$1 $2');

	// 删除中文之间的空格
	text = text.replace(/([0-9\.\u4e00-\u9fa5])\s+([0-9\.\u4e00-\u9fa5])/g, '$1$2');
	text = text.replace(/([0-9\.\u4e00-\u9fa5])\s+([0-9\.\u4e00-\u9fa5])/g, '$1$2');
	text = text.replace(/([\u4e00-\u9fa5])\s+/g, '$1');
	text = text.replace(/\s+([\u4e00-\u9fa5])/g, '$1');

	// // 在中英文之间添加空格
	// text = text.replace(/([\u4e00-\u9fa5])([a-zA-Z])/g, '$1 $2');
	// text = text.replace(/([a-zA-Z])([\u4e00-\u9fa5])/g, '$1 $2');

	return text;
}

function match_zotero_color(text) {
	const regex = /#[a-zA-Z0-9]{6}/;
	const matches = text.match(regex);
	return matches ? matches[0] : "";
}

function match_zotero_txt(text) {
	const regex = /“(.*)” \(/;
	const matches = text.match(regex);
	return matches ? matches[1] : "";
}

function match_zotero_author(text) {
	const regex = /\(\[(.*\d+)]\(/;
	const matches = text.match(regex);
	return matches ? matches[1] : "";
}

function match_zotero_link(text) {
	const regex = /\[pdf\]\((.*)\)\)/;
	const matches = text.match(regex);
	return matches ? matches[1] : "";
}

function match_zotero_comment(text) {
	const regex = /.*\)\).*\)\)([\s\S]*)/;
	const matches = text.match(regex);
	return matches ? matches[1] : "";
}

function match_zotero_image(text) {
	const regex = /annotation=(\w*)/;
	const matches = text.match(regex);
	return matches ? matches[1] : "";
}
