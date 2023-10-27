---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==


# Text Elements
实现int指令之前： ^j0cZZWgS

difftest的eip跳转到0x00008f02，这个地址是
异常处理函数的入口地址 ^UrkUefRl

           |               |
           |   Entry Point |<----+
           |               |     |
           |               |     |
           |               |     |
           +---------------+     |
           |               |     |
           |               |     |
           |               |     |
           +---------------+     |
           |offset |       |     |
           |-------+-------|     |
           |       | offset|-----+
  index--->+---------------+
           |               |
           |Gate Descriptor|
           |               |
    IDT--->+---------------+
           |               |
           |               | ^Wsko5ohZ

1. 从IDTR中读出IDT的首地址
2. 根据异常号在IDT中进行索引, 找到一个门描述符
3. 将门描述符中的offset域组合成异常入口地址
4. 依次将eflags, cs(代码段寄存器), eip(也就是PC)寄存器的值压栈
5. 跳转到异常入口地址 ^5Q0eGnLA

static inline void set_idt(void *idt, int size) {
  static volatile struct {
    int16_t size;
    void *idt;
  } __attribute__((packed)) data;
  data.size = size;
  data.idt = idt;
  asm volatile ("lidt (%0)" : : "r"(&data));
}
 ^jILZlWyK

因此可得, size == 0x800, base == 0x10b020 ^9Nkw3UIS

从此为止开始就是idt表的内容了 ^qkMxsLu4

那么 0x81 的地址就是
0x10b020 + 8 * 0x81
= 0x10b020 + 0x408
= 0x10b428 ^4FD8GdII

这个地址是很明显的错误地址，
但difftest为什么执行int 0x81 后会到这个地址呢？ ^5tA1NrCL


# Embedded files
109b035520fb1567e2e4948a862a62ebb89e2856: [[Pasted Image 20231017105549_288.png]]
bcee675d21e1fa3c69de0e739f9a4ff632759f2e: [[Pasted Image 20231017110122_391.png]]
01cb54f040e36492f0a5e800c6da2411bfff9cd4: [[Pasted Image 20231017110856_510.png]]
dc60544f07bed37f87acb6cffc683aecc980fd82: [[Pasted Image 20231017111404_608.png]]

%%
# Drawing
```json
{
	"type": "excalidraw",
	"version": 2,
	"source": "https://github.com/zsviczian/obsidian-excalidraw-plugin/releases/tag/1.9.24",
	"elements": [
		{
			"type": "text",
			"version": 409,
			"versionNonce": 1452939663,
			"isDeleted": false,
			"id": "Wsko5ohZ",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -315.26134634537686,
			"y": 217.93598956790808,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 231.29296875,
			"height": 278.73789503072425,
			"seed": 2056794383,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697511707338,
			"link": null,
			"locked": false,
			"fontSize": 11.61407895961351,
			"fontFamily": 3,
			"text": "           |               |\n           |   Entry Point |<----+\n           |               |     |\n           |               |     |\n           |               |     |\n           +---------------+     |\n           |               |     |\n           |               |     |\n           |               |     |\n           +---------------+     |\n           |offset |       |     |\n           |-------+-------|     |\n           |       | offset|-----+\n  index--->+---------------+\n           |               |\n           |Gate Descriptor|\n           |               |\n    IDT--->+---------------+\n           |               |\n           |               |",
			"rawText": "           |               |\n           |   Entry Point |<----+\n           |               |     |\n           |               |     |\n           |               |     |\n           +---------------+     |\n           |               |     |\n           |               |     |\n           |               |     |\n           +---------------+     |\n           |offset |       |     |\n           |-------+-------|     |\n           |       | offset|-----+\n  index--->+---------------+\n           |               |\n           |Gate Descriptor|\n           |               |\n    IDT--->+---------------+\n           |               |\n           |               |",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "           |               |\n           |   Entry Point |<----+\n           |               |     |\n           |               |     |\n           |               |     |\n           +---------------+     |\n           |               |     |\n           |               |     |\n           |               |     |\n           +---------------+     |\n           |offset |       |     |\n           |-------+-------|     |\n           |       | offset|-----+\n  index--->+---------------+\n           |               |\n           |Gate Descriptor|\n           |               |\n    IDT--->+---------------+\n           |               |\n           |               |",
			"lineHeight": 1.2,
			"baseline": 276
		},
		{
			"type": "text",
			"version": 175,
			"versionNonce": 42769846,
			"isDeleted": false,
			"id": "5Q0eGnLA",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -48.92799651876658,
			"y": 233.50090629449738,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 562.001953125,
			"height": 120,
			"seed": 1658838959,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697878632808,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 4,
			"text": "1. 从IDTR中读出IDT的首地址\n2. 根据异常号在IDT中进行索引, 找到一个门描述符\n3. 将门描述符中的offset域组合成异常入口地址\n4. 依次将eflags, cs(代码段寄存器), eip(也就是PC)寄存器的值压栈\n5. 跳转到异常入口地址",
			"rawText": "1. 从IDTR中读出IDT的首地址\n2. 根据异常号在IDT中进行索引, 找到一个门描述符\n3. 将门描述符中的offset域组合成异常入口地址\n4. 依次将eflags, cs(代码段寄存器), eip(也就是PC)寄存器的值压栈\n5. 跳转到异常入口地址",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "1. 从IDTR中读出IDT的首地址\n2. 根据异常号在IDT中进行索引, 找到一个门描述符\n3. 将门描述符中的offset域组合成异常入口地址\n4. 依次将eflags, cs(代码段寄存器), eip(也就是PC)寄存器的值压栈\n5. 跳转到异常入口地址",
			"lineHeight": 1.2,
			"baseline": 115
		},
		{
			"type": "image",
			"version": 270,
			"versionNonce": 582445953,
			"isDeleted": false,
			"id": "6AHy--tti23nkONUrbyq8",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -309.5870476773141,
			"y": 505.13329174002536,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 262.5092182963411,
			"height": 201.887386105025,
			"seed": 1496367937,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697513158219,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "bcee675d21e1fa3c69de0e739f9a4ff632759f2e",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "text",
			"version": 131,
			"versionNonce": 715773089,
			"isDeleted": false,
			"id": "jILZlWyK",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -24.03355329533221,
			"y": 518.7663058184322,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 324.146484375,
			"height": 135.56910218605577,
			"seed": 665295329,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697511729572,
			"link": null,
			"locked": false,
			"fontSize": 11.297425182171315,
			"fontFamily": 3,
			"text": "static inline void set_idt(void *idt, int size) {\n  static volatile struct {\n    int16_t size;\n    void *idt;\n  } __attribute__((packed)) data;\n  data.size = size;\n  data.idt = idt;\n  asm volatile (\"lidt (%0)\" : : \"r\"(&data));\n}\n",
			"rawText": "static inline void set_idt(void *idt, int size) {\n  static volatile struct {\n    int16_t size;\n    void *idt;\n  } __attribute__((packed)) data;\n  data.size = size;\n  data.idt = idt;\n  asm volatile (\"lidt (%0)\" : : \"r\"(&data));\n}\n",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "static inline void set_idt(void *idt, int size) {\n  static volatile struct {\n    int16_t size;\n    void *idt;\n  } __attribute__((packed)) data;\n  data.size = size;\n  data.idt = idt;\n  asm volatile (\"lidt (%0)\" : : \"r\"(&data));\n}\n",
			"lineHeight": 1.2,
			"baseline": 133
		},
		{
			"type": "arrow",
			"version": 306,
			"versionNonce": 1289160609,
			"isDeleted": false,
			"id": "FEje6kfwtAMXhL9pC4kGF",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -157.19219327070192,
			"y": 644.4867826053255,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 153.15197760952026,
			"height": 92.34807958312024,
			"seed": 721576865,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697513158219,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": null,
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": null,
			"points": [
				[
					0,
					0
				],
				[
					153.15197760952026,
					-92.34807958312024
				]
			]
		},
		{
			"type": "text",
			"version": 336,
			"versionNonce": 811450538,
			"isDeleted": false,
			"id": "9Nkw3UIS",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -35.261036427229016,
			"y": 650.4021413542242,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 372.48046875,
			"height": 24,
			"seed": 144932495,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697878632810,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 4,
			"text": "因此可得, size == 0x800, base == 0x10b020",
			"rawText": "因此可得, size == 0x800, base == 0x10b020",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "因此可得, size == 0x800, base == 0x10b020",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "line",
			"version": 136,
			"versionNonce": 1833154561,
			"isDeleted": false,
			"id": "Io3r2AejMrhVSGG3AI0UQ",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -276.3679804069743,
			"y": 684.3373890170519,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 8.567374604353063,
			"height": 75.83753798262967,
			"seed": 1541299343,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697512039069,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": null,
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": null,
			"points": [
				[
					0,
					0
				],
				[
					-8.567374604353063,
					75.83753798262967
				]
			]
		},
		{
			"type": "text",
			"version": 250,
			"versionNonce": 1574663926,
			"isDeleted": false,
			"id": "qkMxsLu4",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -295.77651435410485,
			"y": 755.693328066501,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 245.791015625,
			"height": 24,
			"seed": 1856379823,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697878632810,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 4,
			"text": "从此为止开始就是idt表的内容了",
			"rawText": "从此为止开始就是idt表的内容了",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "从此为止开始就是idt表的内容了",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "image",
			"version": 154,
			"versionNonce": 1622572705,
			"isDeleted": false,
			"id": "eR7QF1uK73PBdCzoab16x",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -297.4731520685025,
			"y": 796.4040898411159,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 346.3565398138354,
			"height": 125.67794444673457,
			"seed": 346715247,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697512134756,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "01cb54f040e36492f0a5e800c6da2411bfff9cd4",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "text",
			"version": 103,
			"versionNonce": 418650986,
			"isDeleted": false,
			"id": "4FD8GdII",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 85.21876845554709,
			"y": 802.1431878631518,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 180.52734375,
			"height": 96,
			"seed": 1885866095,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697878632811,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 4,
			"text": "那么 0x81 的地址就是\n0x10b020 + 8 * 0x81\n= 0x10b020 + 0x408\n= 0x10b428",
			"rawText": "那么 0x81 的地址就是\n0x10b020 + 8 * 0x81\n= 0x10b020 + 0x408\n= 0x10b428",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "那么 0x81 的地址就是\n0x10b020 + 8 * 0x81\n= 0x10b020 + 0x408\n= 0x10b428",
			"lineHeight": 1.2,
			"baseline": 91
		},
		{
			"type": "image",
			"version": 238,
			"versionNonce": 1963879777,
			"isDeleted": false,
			"id": "lWFa5zFhjueDgC8Bq5nbc",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -298.6368827070951,
			"y": 970.0223308559853,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 353.1822803811778,
			"height": 98.28375675765807,
			"seed": 2075249665,
			"groupIds": [],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697512450373,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "dc60544f07bed37f87acb6cffc683aecc980fd82",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "arrow",
			"version": 166,
			"versionNonce": 290120719,
			"isDeleted": false,
			"id": "FMoKL25bLLfJP7lv5OjWl",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -296.85843127026055,
			"y": 887.6542065656341,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 51.885832594895135,
			"height": 148.3809468181031,
			"seed": 1359563041,
			"groupIds": [],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697512464779,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": null,
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": "arrow",
			"points": [
				[
					0,
					0
				],
				[
					-50.99962829162138,
					74.54671434485874
				],
				[
					0.8862043032737574,
					148.3809468181031
				]
			]
		},
		{
			"type": "text",
			"version": 42,
			"versionNonce": 880617526,
			"isDeleted": false,
			"id": "j0cZZWgS",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -228.6484375,
			"y": -170.01171875,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 133.212890625,
			"height": 24,
			"seed": 786355055,
			"groupIds": [
				"UZIuyokPpSD-GeLkANQuY"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697878632811,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 4,
			"text": "实现int指令之前：",
			"rawText": "实现int指令之前：",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "实现int指令之前：",
			"lineHeight": 1.2,
			"baseline": 19
		},
		{
			"type": "image",
			"version": 107,
			"versionNonce": 2023323909,
			"isDeleted": false,
			"id": "TjnNTj4VzGotoZ5VB-ZNV",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -227.68335459183675,
			"y": -133.77734375,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 403.9540816326531,
			"height": 247.421875,
			"seed": 1399744065,
			"groupIds": [
				"UZIuyokPpSD-GeLkANQuY"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697724136137,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "109b035520fb1567e2e4948a862a62ebb89e2856",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "text",
			"version": 131,
			"versionNonce": 997269034,
			"isDeleted": false,
			"id": "UrkUefRl",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": -223.7360679516682,
			"y": 140.7403182496532,
			"strokeColor": "#1e1e1e",
			"backgroundColor": "transparent",
			"width": 338.134765625,
			"height": 48,
			"seed": 946791553,
			"groupIds": [
				"UZIuyokPpSD-GeLkANQuY"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697878632812,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 4,
			"text": "difftest的eip跳转到0x00008f02，这个地址是\n异常处理函数的入口地址",
			"rawText": "difftest的eip跳转到0x00008f02，这个地址是\n异常处理函数的入口地址",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "difftest的eip跳转到0x00008f02，这个地址是\n异常处理函数的入口地址",
			"lineHeight": 1.2,
			"baseline": 43
		},
		{
			"type": "freedraw",
			"version": 212,
			"versionNonce": 795742309,
			"isDeleted": false,
			"id": "ghzY_B-BS24STBwuXP1D8",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 193.45624554689837,
			"y": 139.17896560930444,
			"strokeColor": "#c92a2a",
			"backgroundColor": "#fa5252",
			"width": 61.31581340428577,
			"height": 51.347263776884525,
			"seed": 1562285135,
			"groupIds": [
				"L01ICxhYidnuGPOYIQAyc",
				"UZIuyokPpSD-GeLkANQuY"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697724136137,
			"link": null,
			"locked": false,
			"points": [
				[
					0,
					0
				],
				[
					0.05933763932394984,
					0.17929256354846052
				],
				[
					4.465615503842732,
					3.3992441901129693
				],
				[
					19.356772086824108,
					13.836934003181304
				],
				[
					36.321965581682655,
					27.351681686774334
				],
				[
					49.17548406029546,
					39.23184802640164
				],
				[
					55.863417381951216,
					45.71217860089113
				],
				[
					59.98188557841776,
					49.85895698097545
				],
				[
					60.91476300176208,
					50.87946642916817
				],
				[
					61.13249232688552,
					51.2097571707408
				],
				[
					61.2699989330292,
					51.347263776884525
				],
				[
					61.31581340428577,
					51.347263776884525
				],
				[
					61.31581340428577,
					51.30075418951238
				],
				[
					61.31581340428577,
					51.207735014768055
				],
				[
					61.26930381691362,
					51.068206252651564
				],
				[
					61.176284642169264,
					51.02169666527941
				],
				[
					61.08326546742502,
					50.92867749053509
				],
				[
					61.03675588005282,
					50.88216790316294
				],
				[
					60.990246292680645,
					50.83565831579078
				],
				[
					60.94373670530852,
					50.83565831579078
				],
				[
					60.89722711793639,
					50.78914872841862
				],
				[
					60.89722711793639,
					50.742639141046425
				],
				[
					60.89722711793639,
					50.742639141046425
				]
			],
			"lastCommittedPoint": null,
			"simulatePressure": true,
			"pressures": []
		},
		{
			"type": "freedraw",
			"version": 232,
			"versionNonce": 1384469611,
			"isDeleted": false,
			"id": "OT6BOGLB-pJH5toBxY0bO",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 202.51877614818574,
			"y": 426.935905146776,
			"strokeColor": "#c92a2a",
			"backgroundColor": "#fa5252",
			"width": 48.01811572779399,
			"height": 49.83737678520423,
			"seed": 1074082415,
			"groupIds": [
				"L01ICxhYidnuGPOYIQAyc",
				"UZIuyokPpSD-GeLkANQuY"
			],
			"frameId": null,
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1697724136137,
			"link": null,
			"locked": false,
			"points": [
				[
					-0.2243503645335301,
					-240.40277028674544
				],
				[
					-0.2708599519056683,
					-240.40277028674544
				],
				[
					0.2130988454988075,
					-240.48365652565343
				],
				[
					5.859653437399792,
					-246.10322797379382
				],
				[
					19.207905013209192,
					-261.788412536025
				],
				[
					28.991095609143986,
					-273.08551863749204
				],
				[
					33.612385526697786,
					-278.4354798213344
				],
				[
					35.399971406566735,
					-280.22508785717605
				],
				[
					36.0531277857497,
					-280.68680293888104
				],
				[
					36.30927807435439,
					-280.892399328168
				],
				[
					36.44678468049813,
					-280.98541850291224
				],
				[
					36.851215875038655,
					-281.2253757456418
				],
				[
					37.24079686165457,
					-281.4970239640061
				],
				[
					37.43764110712241,
					-281.6432827139692
				],
				[
					37.52930164582248,
					-281.68979230134136
				],
				[
					37.52930164582248,
					-281.73630188871334
				],
				[
					37.57514771326609,
					-281.73630188871334
				],
				[
					37.80027054616465,
					-281.79630304796603
				],
				[
					38.65630604254638,
					-282.3739603381367
				],
				[
					39.23533776685492,
					-282.768960070836
				],
				[
					39.58649778998955,
					-283.06958199274646
				],
				[
					39.7240043961333,
					-283.1160915801187
				],
				[
					40.00173488050917,
					-283.34189373103925
				],
				[
					40.4654721181866,
					-283.68768240237137
				],
				[
					40.73577749860014,
					-283.96741924462646
				],
				[
					40.93259014788082,
					-284.1136937926831
				],
				[
					41.115942821468195,
					-284.25322255479955
				],
				[
					41.16175729272478,
					-284.2997321421718
				],
				[
					41.709098041398626,
					-284.901655304015
				],
				[
					42.52604905437042,
					-285.8015147118677
				],
				[
					43.140120950143434,
					-286.4775941247723
				],
				[
					43.47712588146914,
					-286.8092277042956
				],
				[
					43.90177863573673,
					-287.24331192040455
				],
				[
					44.164658912187996,
					-287.5082143528286
				],
				[
					44.48011524392958,
					-287.7731167852527
				],
				[
					44.964769157449666,
					-288.19979169549276
				],
				[
					45.54310576564259,
					-288.63321239167317
				],
				[
					46.700442501956935,
					-289.57283560095783
				],
				[
					47.174322115684966,
					-289.91457996034455
				],
				[
					47.56390310230096,
					-290.19363748457755
				],
				[
					47.70140970844474,
					-290.24014707194965
				],
				[
					47.74725577588832,
					-290.24014707194965
				],
				[
					47.74725577588832,
					-290.24014707194965
				]
			],
			"lastCommittedPoint": null,
			"simulatePressure": true,
			"pressures": []
		},
		{
			"type": "text",
			"version": 171,
			"versionNonce": 1180086646,
			"isDeleted": false,
			"id": "5tA1NrCL",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 1,
			"opacity": 100,
			"angle": 0,
			"x": 229.3327629941324,
			"y": 37.123728050916554,
			"strokeColor": "#e03131",
			"backgroundColor": "transparent",
			"width": 398.90625,
			"height": 48,
			"seed": 675937391,
			"groupIds": [
				"UZIuyokPpSD-GeLkANQuY"
			],
			"frameId": null,
			"roundness": null,
			"boundElements": [],
			"updated": 1697878632812,
			"link": null,
			"locked": false,
			"fontSize": 20,
			"fontFamily": 4,
			"text": "这个地址是很明显的错误地址，\n但difftest为什么执行int 0x81 后会到这个地址呢？",
			"rawText": "这个地址是很明显的错误地址，\n但difftest为什么执行int 0x81 后会到这个地址呢？",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "这个地址是很明显的错误地址，\n但difftest为什么执行int 0x81 后会到这个地址呢？",
			"lineHeight": 1.2,
			"baseline": 43
		}
	],
	"appState": {
		"theme": "light",
		"viewBackgroundColor": "#ffffff",
		"currentItemStrokeColor": "#e03131",
		"currentItemBackgroundColor": "transparent",
		"currentItemFillStyle": "hachure",
		"currentItemStrokeWidth": 1,
		"currentItemStrokeStyle": "solid",
		"currentItemRoughness": 1,
		"currentItemOpacity": 100,
		"currentItemFontFamily": 4,
		"currentItemFontSize": 20,
		"currentItemTextAlign": "left",
		"currentItemStartArrowhead": null,
		"currentItemEndArrowhead": "arrow",
		"scrollX": 723.9026710065324,
		"scrollY": 245.85281556817824,
		"zoom": {
			"value": 0.7000000000000001
		},
		"currentItemRoundness": "round",
		"gridSize": null,
		"gridColor": {
			"Bold": "#C9C9C9FF",
			"Regular": "#EDEDEDFF"
		},
		"currentStrokeOptions": null,
		"previousGridSize": null,
		"frameRendering": {
			"enabled": true,
			"clip": true,
			"name": true,
			"outline": true
		}
	},
	"files": {}
}
```
%%