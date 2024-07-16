---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==


# Text Elements
level 1 的目的就是改变程序返回地址，本应该返回到 test 函数的 401976
我们的攻击代码通过改变栈上的内容让 getbuf 返回到 touch1的开始位置 ^0UoLTnef

可以看到返回地址在这里，所以我们构造的字符串溢出
后把这里覆盖为touch1的地址就行了 ^qomROJOt


# Embedded files
65707195a406a98851bea80bc83d49f8678ddb17: [[Pasted Image 20230207134637_220.png]]
0ab8c93e3eb3ad970cd8ac6052090b9bf8b21a3e: [[Pasted Image 20230207134810_252.png]]
025c87d987289733bc4dbab89f9ad8fbce531d2a: [[Pasted Image 20230207135139_339.png]]

%%
# Drawing
```json
{
	"type": "excalidraw",
	"version": 2,
	"source": "https://github.com/zsviczian/obsidian-excalidraw-plugin/releases/tag/1.9.3",
	"elements": [
		{
			"type": "image",
			"version": 39,
			"versionNonce": 20101794,
			"isDeleted": false,
			"id": "2tPk-5o-0iGRyLSEDkaA6",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": -486.93419471153857,
			"y": -215.3359375,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 708.923076923077,
			"height": 352,
			"seed": 619174306,
			"groupIds": [],
			"roundness": null,
			"boundElements": [],
			"updated": 1675749091144,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "65707195a406a98851bea80bc83d49f8678ddb17",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "image",
			"version": 110,
			"versionNonce": 1818572926,
			"isDeleted": false,
			"id": "sgXzg3pOWromuFcJ3KXF4",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": -488.8090057665505,
			"y": 141.8005386404235,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 716.4229809064873,
			"height": 282.0915487319294,
			"seed": 735202110,
			"groupIds": [],
			"roundness": null,
			"boundElements": [],
			"updated": 1675749091144,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "0ab8c93e3eb3ad970cd8ac6052090b9bf8b21a3e",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "text",
			"version": 393,
			"versionNonce": 2014570138,
			"isDeleted": false,
			"id": "0UoLTnef",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": 349.0081140801699,
			"y": 316.7138363928846,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"width": 900.703125,
			"height": 67.2,
			"seed": 1783591550,
			"groupIds": [],
			"roundness": null,
			"boundElements": [
				{
					"id": "-AbhpHCLfZwG7q5Q5IyZD",
					"type": "arrow"
				}
			],
			"updated": 1687083690530,
			"link": null,
			"locked": false,
			"customData": {
				"legacyTextWrap": true
			},
			"fontSize": 28,
			"fontFamily": 4,
			"text": "level 1 的目的就是改变程序返回地址，本应该返回到 test 函数的 401976\n我们的攻击代码通过改变栈上的内容让 getbuf 返回到 touch1的开始位置",
			"rawText": "level 1 的目的就是改变程序返回地址，本应该返回到 test 函数的 401976\n我们的攻击代码通过改变栈上的内容让 getbuf 返回到 touch1的开始位置",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "level 1 的目的就是改变程序返回地址，本应该返回到 test 函数的 401976\n我们的攻击代码通过改变栈上的内容让 getbuf 返回到 touch1的开始位置",
			"lineHeight": 1.2,
			"baseline": 60
		},
		{
			"type": "arrow",
			"version": 329,
			"versionNonce": 882971746,
			"isDeleted": false,
			"id": "-AbhpHCLfZwG7q5Q5IyZD",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": 5.212657876501282,
			"y": 204.47076519792654,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"width": 447.0343100178607,
			"height": 106.9271061950987,
			"seed": 2137195262,
			"groupIds": [],
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1675749091146,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": {
				"elementId": "0UoLTnef",
				"focus": -0.08821911676241546,
				"gap": 14.515964999859364
			},
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": "triangle",
			"points": [
				[
					0,
					0
				],
				[
					447.0343100178607,
					106.9271061950987
				]
			]
		},
		{
			"type": "arrow",
			"version": 105,
			"versionNonce": 1353564450,
			"isDeleted": false,
			"id": "URRPp36azrFEz9twUDWQL",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": 3.0259734471100046,
			"y": -173.03307779783285,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"width": 383.31680033599326,
			"height": 27.192706410560845,
			"seed": 785949474,
			"groupIds": [],
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1675749098914,
			"link": null,
			"locked": false,
			"startBinding": null,
			"endBinding": {
				"elementId": "2p3d9NyFCvTRRbu4s_MUz",
				"gap": 11.117738588273582,
				"focus": 0.10452769321060258
			},
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": "triangle",
			"points": [
				[
					0,
					0
				],
				[
					383.31680033599326,
					-27.192706410560845
				]
			]
		},
		{
			"type": "image",
			"version": 121,
			"versionNonce": 1332134334,
			"isDeleted": false,
			"id": "2p3d9NyFCvTRRbu4s_MUz",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": 397.46051237137686,
			"y": -329.2052221668272,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"width": 587.1706783988571,
			"height": 244.65444933285715,
			"seed": 1771328254,
			"groupIds": [],
			"roundness": null,
			"boundElements": [
				{
					"id": "URRPp36azrFEz9twUDWQL",
					"type": "arrow"
				}
			],
			"updated": 1675749098898,
			"link": null,
			"locked": false,
			"customData": {
				"legacyTextWrap": true
			},
			"status": "pending",
			"fileId": "025c87d987289733bc4dbab89f9ad8fbce531d2a",
			"scale": [
				1,
				1
			]
		},
		{
			"type": "text",
			"version": 247,
			"versionNonce": 100036314,
			"isDeleted": false,
			"id": "qomROJOt",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": 411.6702154063411,
			"y": 27.32712490809992,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"width": 672,
			"height": 67.2,
			"seed": 1274081982,
			"groupIds": [],
			"roundness": null,
			"boundElements": [
				{
					"id": "LZ4dHtigQpAZ_KgdqBjqd",
					"type": "arrow"
				}
			],
			"updated": 1687083686620,
			"link": null,
			"locked": false,
			"customData": {
				"legacyTextWrap": true
			},
			"fontSize": 28,
			"fontFamily": 4,
			"text": "可以看到返回地址在这里，所以我们构造的字符串溢出\n后把这里覆盖为touch1的地址就行了",
			"rawText": "可以看到返回地址在这里，所以我们构造的字符串溢出\n后把这里覆盖为touch1的地址就行了",
			"textAlign": "left",
			"verticalAlign": "top",
			"containerId": null,
			"originalText": "可以看到返回地址在这里，所以我们构造的字符串溢出\n后把这里覆盖为touch1的地址就行了",
			"lineHeight": 1.2,
			"baseline": 60
		},
		{
			"type": "rectangle",
			"version": 71,
			"versionNonce": 490925858,
			"isDeleted": false,
			"id": "kMfGH1nwzeWzeqrz_OMzT",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": 704.825150883179,
			"y": -134.0901876436032,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"width": 151.4504134605752,
			"height": 15.967842212097707,
			"seed": 947871266,
			"groupIds": [],
			"roundness": {
				"type": 3
			},
			"boundElements": [
				{
					"id": "LZ4dHtigQpAZ_KgdqBjqd",
					"type": "arrow"
				}
			],
			"updated": 1675749124823,
			"link": null,
			"locked": false,
			"customData": {
				"legacyTextWrap": true
			}
		},
		{
			"type": "arrow",
			"version": 505,
			"versionNonce": 1572307866,
			"isDeleted": false,
			"id": "LZ4dHtigQpAZ_KgdqBjqd",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": 733.9882305414031,
			"y": -114.2233962152721,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"width": 60.02718361071766,
			"height": 130.8703424194272,
			"seed": 353874274,
			"groupIds": [],
			"roundness": {
				"type": 2
			},
			"boundElements": [],
			"updated": 1687083686620,
			"link": null,
			"locked": false,
			"startBinding": {
				"elementId": "kMfGH1nwzeWzeqrz_OMzT",
				"focus": 0.6545416001636066,
				"gap": 3.8989492162334045
			},
			"endBinding": {
				"elementId": "qomROJOt",
				"focus": 0.18967927892002454,
				"gap": 10.680178703944819
			},
			"lastCommittedPoint": null,
			"startArrowhead": null,
			"endArrowhead": "triangle",
			"points": [
				[
					0,
					0
				],
				[
					60.02718361071766,
					130.8703424194272
				]
			]
		},
		{
			"type": "freedraw",
			"version": 6,
			"versionNonce": 942013594,
			"isDeleted": true,
			"id": "guwoQ3-A5J06QLfxAOR13",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"angle": 0,
			"x": 173.2578125,
			"y": -332.13671875,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"width": 0.0001,
			"height": 0.0001,
			"seed": 1937669630,
			"groupIds": [],
			"roundness": null,
			"boundElements": [],
			"updated": 1687083656351,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"smoothing": 0.2,
						"thinning": 0.6,
						"streamline": 0.2,
						"easing": "easeInOutSine",
						"start": {
							"taper": 150,
							"cap": true,
							"easing": "linear"
						},
						"end": {
							"taper": 1,
							"cap": true,
							"easing": "linear"
						}
					}
				}
			},
			"points": [
				[
					0,
					0
				],
				[
					0.0001,
					0.0001
				]
			],
			"lastCommittedPoint": null,
			"simulatePressure": true,
			"pressures": []
		}
	],
	"appState": {
		"theme": "light",
		"viewBackgroundColor": "#ffffff",
		"currentItemStrokeColor": "#c92a2a",
		"currentItemBackgroundColor": "transparent",
		"currentItemFillStyle": "hachure",
		"currentItemStrokeWidth": 2,
		"currentItemStrokeStyle": "solid",
		"currentItemRoughness": 0,
		"currentItemOpacity": 100,
		"currentItemFontFamily": 4,
		"currentItemFontSize": 28,
		"currentItemTextAlign": "left",
		"currentItemStartArrowhead": null,
		"currentItemEndArrowhead": "triangle",
		"scrollX": 187.46480775800808,
		"scrollY": 523.8254304998158,
		"zoom": {
			"value": 0.802021998359194
		},
		"currentItemRoundness": "round",
		"gridSize": null,
		"colorPalette": {},
		"currentStrokeOptions": {
			"highlighter": false,
			"constantPressure": false,
			"hasOutline": false,
			"outlineWidth": 0,
			"options": {
				"smoothing": 0.2,
				"thinning": 0.6,
				"streamline": 0.2,
				"easing": "easeInOutSine",
				"start": {
					"taper": 150,
					"cap": true,
					"easing": "linear"
				},
				"end": {
					"taper": 1,
					"cap": true,
					"easing": "linear"
				}
			}
		},
		"previousGridSize": null
	},
	"files": {}
}
```
%%