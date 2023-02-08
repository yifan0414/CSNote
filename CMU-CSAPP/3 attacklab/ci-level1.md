---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==


# Text Elements
level 1 的目的就是改变程序返回地址，本应该返回到 test 函数的 401976
我们的攻击代码通过改变栈上的内容让 getbuf 返回到 touch1的开始位置 ^0UoLTnef

可以看到返回地址在这里，所以我们构造的字符串溢出后把这里覆盖为touch1的地址就行了 ^qomROJOt


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
	"source": "https://excalidraw.com",
	"elements": [
		{
			"id": "guwoQ3-A5J06QLfxAOR13",
			"type": "freedraw",
			"x": 173.2578125,
			"y": -332.13671875,
			"width": 0.0001,
			"height": 0.0001,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": null,
			"seed": 1937669630,
			"version": 5,
			"versionNonce": 1766977598,
			"isDeleted": false,
			"boundElements": null,
			"updated": 1675749091144,
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
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				0.0001,
				0.0001
			]
		},
		{
			"id": "2tPk-5o-0iGRyLSEDkaA6",
			"type": "image",
			"x": -486.93419471153857,
			"y": -215.3359375,
			"width": 708.923076923077,
			"height": 352,
			"angle": 0,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": null,
			"seed": 619174306,
			"version": 39,
			"versionNonce": 20101794,
			"isDeleted": false,
			"boundElements": null,
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
			"id": "sgXzg3pOWromuFcJ3KXF4",
			"type": "image",
			"x": -488.8090057665505,
			"y": 141.8005386404235,
			"width": 716.4229809064873,
			"height": 282.0915487319294,
			"angle": 0,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": null,
			"seed": 735202110,
			"version": 110,
			"versionNonce": 1818572926,
			"isDeleted": false,
			"boundElements": null,
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
			"id": "0UoLTnef",
			"type": "text",
			"x": 349.0081140801699,
			"y": 325.9138363928846,
			"width": 639,
			"height": 56,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": null,
			"seed": 1783591550,
			"version": 388,
			"versionNonce": 526801534,
			"isDeleted": false,
			"boundElements": [
				{
					"id": "-AbhpHCLfZwG7q5Q5IyZD",
					"type": "arrow"
				}
			],
			"updated": 1675749091146,
			"link": null,
			"locked": false,
			"text": "level 1 的目的就是改变程序返回地址，本应该返回到 test 函数的 401976\n我们的攻击代码通过改变栈上的内容让 getbuf 返回到 touch1的开始位置",
			"rawText": "level 1 的目的就是改变程序返回地址，本应该返回到 test 函数的 401976\n我们的攻击代码通过改变栈上的内容让 getbuf 返回到 touch1的开始位置",
			"fontSize": 20,
			"fontFamily": 2,
			"textAlign": "left",
			"verticalAlign": "top",
			"baseline": 49,
			"containerId": null,
			"originalText": "level 1 的目的就是改变程序返回地址，本应该返回到 test 函数的 401976\n我们的攻击代码通过改变栈上的内容让 getbuf 返回到 touch1的开始位置"
		},
		{
			"id": "-AbhpHCLfZwG7q5Q5IyZD",
			"type": "arrow",
			"x": 5.212657876501282,
			"y": 204.47076519792654,
			"width": 447.0343100178607,
			"height": 106.9271061950987,
			"angle": 0,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": {
				"type": 2
			},
			"seed": 2137195262,
			"version": 329,
			"versionNonce": 882971746,
			"isDeleted": false,
			"boundElements": null,
			"updated": 1675749091146,
			"link": null,
			"locked": false,
			"points": [
				[
					0,
					0
				],
				[
					447.0343100178607,
					106.9271061950987
				]
			],
			"lastCommittedPoint": null,
			"startBinding": null,
			"endBinding": {
				"elementId": "0UoLTnef",
				"focus": -0.08821911676241546,
				"gap": 14.515964999859364
			},
			"startArrowhead": null,
			"endArrowhead": "triangle"
		},
		{
			"id": "URRPp36azrFEz9twUDWQL",
			"type": "arrow",
			"x": 3.0259734471100046,
			"y": -173.03307779783285,
			"width": 383.31680033599326,
			"height": 27.192706410560845,
			"angle": 0,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": {
				"type": 2
			},
			"seed": 785949474,
			"version": 105,
			"versionNonce": 1353564450,
			"isDeleted": false,
			"boundElements": null,
			"updated": 1675749098914,
			"link": null,
			"locked": false,
			"points": [
				[
					0,
					0
				],
				[
					383.31680033599326,
					-27.192706410560845
				]
			],
			"lastCommittedPoint": null,
			"startBinding": null,
			"endBinding": {
				"elementId": "2p3d9NyFCvTRRbu4s_MUz",
				"gap": 11.117738588273582,
				"focus": 0.10452769321060258
			},
			"startArrowhead": null,
			"endArrowhead": "triangle"
		},
		{
			"id": "2p3d9NyFCvTRRbu4s_MUz",
			"type": "image",
			"x": 397.46051237137686,
			"y": -329.2052221668272,
			"width": 587.1706783988571,
			"height": 244.65444933285715,
			"angle": 0,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": null,
			"seed": 1771328254,
			"version": 121,
			"versionNonce": 1332134334,
			"isDeleted": false,
			"boundElements": [
				{
					"id": "URRPp36azrFEz9twUDWQL",
					"type": "arrow"
				}
			],
			"updated": 1675749098898,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "025c87d987289733bc4dbab89f9ad8fbce531d2a",
			"scale": [
				1,
				1
			]
		},
		{
			"id": "qomROJOt",
			"type": "text",
			"x": 324.3908139146008,
			"y": 43.34876224275223,
			"width": 801,
			"height": 28,
			"angle": 0,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": null,
			"seed": 1274081982,
			"version": 204,
			"versionNonce": 2123645986,
			"isDeleted": false,
			"boundElements": [
				{
					"id": "LZ4dHtigQpAZ_KgdqBjqd",
					"type": "arrow"
				}
			],
			"updated": 1675749168998,
			"link": null,
			"locked": false,
			"text": "可以看到返回地址在这里，所以我们构造的字符串溢出后把这里覆盖为touch1的地址就行了",
			"rawText": "可以看到返回地址在这里，所以我们构造的字符串溢出后把这里覆盖为touch1的地址就行了",
			"fontSize": 20,
			"fontFamily": 2,
			"textAlign": "left",
			"verticalAlign": "top",
			"baseline": 21,
			"containerId": null,
			"originalText": "可以看到返回地址在这里，所以我们构造的字符串溢出后把这里覆盖为touch1的地址就行了"
		},
		{
			"id": "kMfGH1nwzeWzeqrz_OMzT",
			"type": "rectangle",
			"x": 704.825150883179,
			"y": -134.0901876436032,
			"width": 151.4504134605752,
			"height": 15.967842212097707,
			"angle": 0,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": {
				"type": 3
			},
			"seed": 947871266,
			"version": 71,
			"versionNonce": 490925858,
			"isDeleted": false,
			"boundElements": [
				{
					"id": "LZ4dHtigQpAZ_KgdqBjqd",
					"type": "arrow"
				}
			],
			"updated": 1675749124823,
			"link": null,
			"locked": false
		},
		{
			"id": "LZ4dHtigQpAZ_KgdqBjqd",
			"type": "arrow",
			"x": 733.4794715806808,
			"y": -114.2233962152721,
			"width": 58.59263878800277,
			"height": 146.8919797540795,
			"angle": 0,
			"strokeColor": "#c92a2a",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": {
				"type": 2
			},
			"seed": 353874274,
			"version": 453,
			"versionNonce": 494628834,
			"isDeleted": false,
			"boundElements": null,
			"updated": 1675749168999,
			"link": null,
			"locked": false,
			"points": [
				[
					0,
					0
				],
				[
					58.59263878800277,
					146.8919797540795
				]
			],
			"lastCommittedPoint": null,
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
			"startArrowhead": null,
			"endArrowhead": "triangle"
		},
		{
			"id": "1VhTG8izoSiIpRngsYviR",
			"type": "freedraw",
			"x": -123.51171875,
			"y": -105.4921875,
			"width": 311.92578125,
			"height": 143.9453125,
			"angle": 0,
			"strokeColor": "#FFC47C",
			"backgroundColor": "#FFC47C",
			"fillStyle": "solid",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": null,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 2021641890,
			"version": 48,
			"versionNonce": 1644631650,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091144,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": true,
					"constantPressure": true,
					"hasOutline": true,
					"outlineWidth": 4,
					"options": {
						"thinning": 1,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "linear",
						"start": {
							"taper": 0,
							"cap": true,
							"easing": "linear"
						},
						"end": {
							"taper": 0,
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
					19.51171875,
					2.18359375
				],
				[
					80.61328125,
					4.765625
				],
				[
					135.86328125,
					4.765625
				],
				[
					162.73828125,
					6.109375
				],
				[
					222.33203125,
					6.109375
				],
				[
					243.04296875,
					6.109375
				],
				[
					250.234375,
					5.66015625
				],
				[
					258.765625,
					4.23046875
				],
				[
					264.453125,
					2.08984375
				],
				[
					271.64453125,
					-0.20703125
				],
				[
					281.83984375,
					-3.03125
				],
				[
					293.37890625,
					-6.19921875
				],
				[
					301.203125,
					-9.68359375
				],
				[
					307.68359375,
					-13.5625
				],
				[
					310.87109375,
					-17.66015625
				],
				[
					311.48046875,
					-20.234375
				],
				[
					311.92578125,
					-21.58203125
				],
				[
					311.92578125,
					-24.27734375
				],
				[
					311.92578125,
					-28.47265625
				],
				[
					310.5,
					-32.66796875
				],
				[
					303.5078125,
					-40.98046875
				],
				[
					295.67578125,
					-46.20703125
				],
				[
					282.46875,
					-50.26171875
				],
				[
					269.26171875,
					-52.2890625
				],
				[
					236.68359375,
					-54.55078125
				],
				[
					215.96484375,
					-54.55078125
				],
				[
					184.734375,
					-49.63671875
				],
				[
					150.5,
					-43.30078125
				],
				[
					107.4140625,
					-31.02734375
				],
				[
					86.6953125,
					-23.0234375
				],
				[
					74.5390625,
					-14.8515625
				],
				[
					69.4375,
					-7.20703125
				],
				[
					64.68359375,
					11.84375
				],
				[
					64.68359375,
					25.04296875
				],
				[
					69.109375,
					44.25
				],
				[
					79.48828125,
					55.78125
				],
				[
					104.00390625,
					71.703125
				],
				[
					141.07421875,
					84.6328125
				],
				[
					163.28515625,
					88.15625
				],
				[
					183.9921875,
					89.39453125
				],
				[
					197.3515625,
					88.1796875
				],
				[
					197.3515625,
					88.1796875
				]
			],
			"pressures": [
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				1,
				0
			],
			"simulatePressure": false,
			"lastCommittedPoint": [
				197.3515625,
				88.1796875
			]
		},
		{
			"id": "MOL8R4ocWrOjmbA-bjr2k",
			"type": "freedraw",
			"x": 22.95703125,
			"y": -147.5625,
			"width": 60.31640625,
			"height": 84.484375,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 1889315518,
			"version": 65,
			"versionNonce": 1986361534,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					0.4609375,
					0
				],
				[
					2.296875,
					0
				],
				[
					5.40625,
					0
				],
				[
					9.375,
					0
				],
				[
					14.3515625,
					0
				],
				[
					19.55859375,
					0.3046875
				],
				[
					24.40234375,
					1.359375
				],
				[
					28.59375,
					2.66796875
				],
				[
					31.8203125,
					3.58203125
				],
				[
					34.52734375,
					4.44921875
				],
				[
					36.99609375,
					5.30078125
				],
				[
					39.50390625,
					5.69140625
				],
				[
					42.25,
					5.74609375
				],
				[
					45.26953125,
					5.74609375
				],
				[
					48.2890625,
					5.74609375
				],
				[
					51,
					4.88671875
				],
				[
					53.515625,
					3.1484375
				],
				[
					55.34765625,
					1.4921875
				],
				[
					56.39453125,
					-0.0625
				],
				[
					56.9296875,
					-1.62109375
				],
				[
					57.03515625,
					-3.05859375
				],
				[
					57.03515625,
					-4.42578125
				],
				[
					56.50390625,
					-5.7421875
				],
				[
					55.14453125,
					-7.09765625
				],
				[
					53.0078125,
					-9.28515625
				],
				[
					50.01171875,
					-12.46484375
				],
				[
					46.66015625,
					-15.9296875
				],
				[
					42.5,
					-19.69921875
				],
				[
					37.86328125,
					-22.9296875
				],
				[
					33.5390625,
					-24.52734375
				],
				[
					29.70703125,
					-25.125
				],
				[
					26.88671875,
					-25.3046875
				],
				[
					24.7265625,
					-24.85546875
				],
				[
					22.734375,
					-23.3515625
				],
				[
					20.58203125,
					-21.046875
				],
				[
					18.03125,
					-18.3984375
				],
				[
					14.42578125,
					-15.12109375
				],
				[
					10.04296875,
					-11.15234375
				],
				[
					5.98828125,
					-7.375
				],
				[
					2.15625,
					-3.734375
				],
				[
					-0.796875,
					-0.12890625
				],
				[
					-2.34375,
					2.90234375
				],
				[
					-3.08203125,
					5.62890625
				],
				[
					-3.28125,
					9.61328125
				],
				[
					-3.28125,
					15.390625
				],
				[
					-2.38671875,
					22.75
				],
				[
					0.296875,
					31.39453125
				],
				[
					4.515625,
					40.01171875
				],
				[
					9.77734375,
					47.703125
				],
				[
					15.1171875,
					53.046875
				],
				[
					20.49609375,
					56.30859375
				],
				[
					26.54296875,
					58.45703125
				],
				[
					32.015625,
					59.1796875
				],
				[
					36.109375,
					59.1796875
				],
				[
					39.1171875,
					59.1796875
				],
				[
					40.94140625,
					59.1796875
				],
				[
					42.14453125,
					59.1796875
				],
				[
					43.00390625,
					59.1796875
				],
				[
					43.00390625,
					59.1796875
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				43.00390625,
				59.1796875
			]
		},
		{
			"id": "zhMhmQwNvvuTYUI5Iphlv",
			"type": "freedraw",
			"x": -100.53125,
			"y": -73.91796875,
			"width": 50.703125,
			"height": 21.16796875,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 1671307426,
			"version": 27,
			"versionNonce": 660208162,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					0.32421875,
					0
				],
				[
					2.9609375,
					0
				],
				[
					8.7109375,
					-0.5625
				],
				[
					17.37109375,
					-2.90234375
				],
				[
					28.0859375,
					-6.80859375
				],
				[
					37.1015625,
					-10.87109375
				],
				[
					42.98828125,
					-14.2109375
				],
				[
					46.953125,
					-16.83984375
				],
				[
					49.33203125,
					-18.89453125
				],
				[
					50.265625,
					-20.03515625
				],
				[
					50.5625,
					-20.609375
				],
				[
					50.703125,
					-21.0078125
				],
				[
					50.703125,
					-21.15625
				],
				[
					50.6171875,
					-21.16796875
				],
				[
					50.3203125,
					-21.16796875
				],
				[
					49.6640625,
					-21.16796875
				],
				[
					48.56640625,
					-21.16796875
				],
				[
					47.04296875,
					-21.1015625
				],
				[
					45.06640625,
					-20.703125
				],
				[
					42.7734375,
					-20.203125
				],
				[
					42.7734375,
					-20.203125
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				42.7734375,
				-20.203125
			]
		},
		{
			"id": "BGkQGiPaBE7OXRGsI-0ap",
			"type": "freedraw",
			"x": -90.3203125,
			"y": -91.109375,
			"width": 11.234375,
			"height": 16.77734375,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 1134787902,
			"version": 23,
			"versionNonce": 250851582,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					-0.125,
					0.12109375
				],
				[
					-0.25,
					0.4765625
				],
				[
					-0.25,
					2.08984375
				],
				[
					-0.20703125,
					4.6953125
				],
				[
					0.796875,
					7.3984375
				],
				[
					2.7890625,
					10.2421875
				],
				[
					4.53515625,
					12.375
				],
				[
					5.9453125,
					13.875
				],
				[
					7.1796875,
					14.98046875
				],
				[
					8.0625,
					15.5546875
				],
				[
					8.671875,
					15.96484375
				],
				[
					9.0859375,
					16.22265625
				],
				[
					9.48828125,
					16.39453125
				],
				[
					10,
					16.65234375
				],
				[
					10.51953125,
					16.77734375
				],
				[
					10.984375,
					16.77734375
				],
				[
					10.984375,
					16.77734375
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				10.984375,
				16.77734375
			]
		},
		{
			"id": "zqdLtQUqQ3UUlujGmZmNA",
			"type": "freedraw",
			"x": -107.02734375,
			"y": -43.59765625,
			"width": 166.12109375,
			"height": 30.046875,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 1874294626,
			"version": 15,
			"versionNonce": 1343907298,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					3.296875,
					0
				],
				[
					14.9921875,
					0
				],
				[
					31.1953125,
					-3.14453125
				],
				[
					75.77734375,
					-11.88671875
				],
				[
					102.4921875,
					-19.15625
				],
				[
					135.21484375,
					-25.46875
				],
				[
					154.421875,
					-28.89453125
				],
				[
					166.12109375,
					-30.046875
				],
				[
					166.12109375,
					-30.046875
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				166.12109375,
				-30.046875
			]
		},
		{
			"id": "uhkGjbU4InunDX8e393Vt",
			"type": "freedraw",
			"x": -82.18359375,
			"y": -88.51953125,
			"width": 38.83203125,
			"height": 66.78515625,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 2037453054,
			"version": 18,
			"versionNonce": 563142974,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					0,
					2.6875
				],
				[
					0,
					14.22265625
				],
				[
					3.16015625,
					21.4140625
				],
				[
					8.69140625,
					31.609375
				],
				[
					18.640625,
					47.11328125
				],
				[
					32.91796875,
					62.65234375
				],
				[
					37.00390625,
					65.56640625
				],
				[
					37.91796875,
					65.87109375
				],
				[
					38.22265625,
					66.17578125
				],
				[
					38.52734375,
					66.48046875
				],
				[
					38.83203125,
					66.78515625
				],
				[
					38.83203125,
					66.78515625
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				38.83203125,
				66.78515625
			]
		},
		{
			"id": "8Uhq23FmPJuiooyIzOT1o",
			"type": "freedraw",
			"x": 16.44140625,
			"y": -84.0859375,
			"width": 147.71875,
			"height": 104.9140625,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 809220798,
			"version": 20,
			"versionNonce": 626481570,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					0,
					2.84375
				],
				[
					0,
					14.5390625
				],
				[
					-1.953125,
					26.234375
				],
				[
					-6.12109375,
					40.93359375
				],
				[
					-11.2265625,
					54.1328125
				],
				[
					-19.06640625,
					65.43359375
				],
				[
					-22.1015625,
					68.91015625
				],
				[
					-29.30078125,
					72.94140625
				],
				[
					-54.765625,
					83.8359375
				],
				[
					-88.99609375,
					92.71484375
				],
				[
					-132.0859375,
					102.61328125
				],
				[
					-146.796875,
					104.9140625
				],
				[
					-147.71875,
					104.9140625
				],
				[
					-147.71875,
					104.9140625
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				-147.71875,
				104.9140625
			]
		},
		{
			"id": "KTMUbt7chZzkp_NAFEdNX",
			"type": "freedraw",
			"x": -131.27734375,
			"y": 20.828125,
			"width": 155.70703125,
			"height": 96.65625,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 1592171710,
			"version": 31,
			"versionNonce": 27134334,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					0.609375,
					0
				],
				[
					3.296875,
					-0.8984375
				],
				[
					16.49609375,
					-4.953125
				],
				[
					41.7109375,
					-9.83984375
				],
				[
					92.30078125,
					-18.703125
				],
				[
					129.53125,
					-23.83203125
				],
				[
					142.890625,
					-26.26171875
				],
				[
					154.4296875,
					-28.109375
				],
				[
					154.734375,
					-28.109375
				],
				[
					155.70703125,
					-17.9140625
				],
				[
					155.70703125,
					-4.71484375
				],
				[
					151.40234375,
					15.8359375
				],
				[
					146.2578125,
					26.42578125
				],
				[
					140.40234375,
					38.12109375
				],
				[
					133.359375,
					50.44921875
				],
				[
					121.8359375,
					60.98828125
				],
				[
					111,
					68.546875
				],
				[
					106.8046875,
					68.546875
				],
				[
					102.609375,
					68.546875
				],
				[
					100.6484375,
					68.546875
				],
				[
					99.7265625,
					68.23828125
				],
				[
					94.66015625,
					52.18359375
				],
				[
					89.875,
					26.9609375
				],
				[
					86.09765625,
					10.59375
				],
				[
					86.09765625,
					10.59375
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				86.09765625,
				10.59375
			]
		},
		{
			"id": "pVRWKuHoZf4wpAU9yo6uJ",
			"type": "freedraw",
			"x": -49.8125,
			"y": -3.28125,
			"width": 15.8359375,
			"height": 59.39453125,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 196640482,
			"version": 16,
			"versionNonce": 1983894882,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					0,
					8.6953125
				],
				[
					0,
					20.39453125
				],
				[
					-1.84765625,
					37.94140625
				],
				[
					-3.76953125,
					49.640625
				],
				[
					-6.171875,
					56.83203125
				],
				[
					-6.9296875,
					58.48046875
				],
				[
					-7.8515625,
					59.39453125
				],
				[
					-8.46484375,
					59.0859375
				],
				[
					-15.8359375,
					45.58203125
				],
				[
					-15.8359375,
					45.58203125
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				-15.8359375,
				45.58203125
			]
		},
		{
			"id": "IOgbkAikBPUwgR1VTWJ65",
			"type": "freedraw",
			"x": -76.69921875,
			"y": 15.1171875,
			"width": 101.6484375,
			"height": 44.0859375,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 1125674338,
			"version": 18,
			"versionNonce": 1851533758,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					-1.42578125,
					2.84375
				],
				[
					-3.37890625,
					8.69140625
				],
				[
					-9.3671875,
					27.73828125
				],
				[
					-10.34375,
					33.5859375
				],
				[
					-13.0078125,
					43.78125
				],
				[
					-13.0078125,
					44.0859375
				],
				[
					-10.1640625,
					42.66015625
				],
				[
					-2.41796875,
					38.23046875
				],
				[
					23.0390625,
					26.0703125
				],
				[
					64.76953125,
					14.34765625
				],
				[
					88.640625,
					9.0390625
				],
				[
					88.640625,
					9.0390625
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				88.640625,
				9.0390625
			]
		},
		{
			"id": "dng6YqxLLW0P9O3_8Uwns",
			"type": "freedraw",
			"x": 76.03125,
			"y": 20.875,
			"width": 4.77734375,
			"height": 26.515625,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 1744678818,
			"version": 12,
			"versionNonce": 1411569954,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
			"link": null,
			"locked": false,
			"customData": {
				"strokeOptions": {
					"highlighter": false,
					"constantPressure": false,
					"hasOutline": false,
					"outlineWidth": 0,
					"options": {
						"thinning": 0.2,
						"smoothing": 0.5,
						"streamline": 0.5,
						"easing": "easeOutSine",
						"start": {
							"cap": true,
							"taper": 0,
							"easing": "linear"
						},
						"end": {
							"cap": true,
							"taper": 0,
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
					0.4453125,
					1.34375
				],
				[
					1.3125,
					8.53515625
				],
				[
					4.47265625,
					24.2578125
				],
				[
					4.77734375,
					26.515625
				],
				[
					4.46875,
					26.515625
				],
				[
					4.46875,
					26.515625
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				4.46875,
				26.515625
			]
		},
		{
			"id": "BMMDCdKFfgW5AcgH4BE1N",
			"type": "freedraw",
			"x": 281.58984375,
			"y": -78.734375,
			"width": 215.61328125,
			"height": 147.4453125,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 20,
			"groupIds": [],
			"roundness": null,
			"seed": 780232994,
			"version": 101,
			"versionNonce": 384582142,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091145,
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
					-1.42578125,
					2.84375
				],
				[
					-3.72265625,
					10.03515625
				],
				[
					-6.3359375,
					18.73046875
				],
				[
					-11.00390625,
					28.92578125
				],
				[
					-17.08203125,
					42.125
				],
				[
					-28.546875,
					60.54296875
				],
				[
					-46.171875,
					81.578125
				],
				[
					-50.921875,
					87.1875
				],
				[
					-52.8828125,
					88.38671875
				],
				[
					-54.84375,
					89.5859375
				],
				[
					-57.41796875,
					90.640625
				],
				[
					-59.37890625,
					90.640625
				],
				[
					-59.99609375,
					90.640625
				],
				[
					-60.61328125,
					90.640625
				],
				[
					-63.83984375,
					85.98046875
				],
				[
					-83.62109375,
					59.23046875
				],
				[
					-104.44140625,
					38.41015625
				],
				[
					-112.5,
					30.3515625
				],
				[
					-118.84765625,
					23.02734375
				],
				[
					-118.84765625,
					22.71875
				],
				[
					-118.23828125,
					22.41015625
				],
				[
					-117.62890625,
					22.41015625
				],
				[
					-112.83203125,
					22.85546875
				],
				[
					-97.6328125,
					40.39453125
				],
				[
					-85.4375,
					54.75390625
				],
				[
					-74.84765625,
					67.71484375
				],
				[
					-72.71484375,
					70.15234375
				],
				[
					-72.71484375,
					70.45703125
				],
				[
					-72.71484375,
					71.37109375
				],
				[
					-73.33203125,
					71.98046875
				],
				[
					-73.640625,
					72.28515625
				],
				[
					-74.25390625,
					72.28515625
				],
				[
					-74.5625,
					72.28515625
				],
				[
					-88.96484375,
					72.28515625
				],
				[
					-90.92578125,
					73.7890625
				],
				[
					-92.4375,
					75.7421875
				],
				[
					-93.5,
					77.6953125
				],
				[
					-95.015625,
					80.2578125
				],
				[
					-98.2421875,
					84.34375
				],
				[
					-105.2578125,
					90.375
				],
				[
					-111.74609375,
					95.1171875
				],
				[
					-117.921875,
					99.515625
				],
				[
					-118.23046875,
					99.515625
				],
				[
					-119.15625,
					99.515625
				],
				[
					-120.38671875,
					99.515625
				],
				[
					-116.91015625,
					102.54296875
				],
				[
					-115.69140625,
					103.76171875
				],
				[
					-115.08203125,
					104.37109375
				],
				[
					-114.47265625,
					105.58984375
				],
				[
					-113.05078125,
					111.27734375
				],
				[
					-113.05078125,
					118.30859375
				],
				[
					-113.05078125,
					118.91796875
				],
				[
					-114.11328125,
					120.56640625
				],
				[
					-116.07421875,
					120.56640625
				],
				[
					-119.23046875,
					120.56640625
				],
				[
					-130.78125,
					119.6953125
				],
				[
					-133.4765625,
					118.34765625
				],
				[
					-136.32421875,
					116.921875
				],
				[
					-140.703125,
					112.09375
				],
				[
					-147.11328125,
					90.03125
				],
				[
					-148.22265625,
					72.3203125
				],
				[
					-147.51171875,
					66.625
				],
				[
					-145.86328125,
					65.11328125
				],
				[
					-141.67578125,
					63.6875
				],
				[
					-137.48828125,
					63.6875
				],
				[
					-132.20703125,
					66.8359375
				],
				[
					-128.98828125,
					70.6171875
				],
				[
					-125.93359375,
					75.4375
				],
				[
					-125.22265625,
					78.28125
				],
				[
					-124.88671875,
					91.3203125
				],
				[
					-132.26953125,
					99.671875
				],
				[
					-136.46484375,
					101.98828125
				],
				[
					-138.42578125,
					102.43359375
				],
				[
					-148.47265625,
					101.45703125
				],
				[
					-160.17578125,
					95.60546875
				],
				[
					-178.28515625,
					87.72265625
				],
				[
					-188.0703125,
					80.90625
				],
				[
					-193.51171875,
					77.0859375
				],
				[
					-196.125,
					85.78125
				],
				[
					-202.28125,
					106.33203125
				],
				[
					-207.53515625,
					121.03515625
				],
				[
					-211.890625,
					128.859375
				],
				[
					-213.765625,
					133.046875
				],
				[
					-214.99609375,
					134.5703125
				],
				[
					-215.61328125,
					134.875
				],
				[
					-214.26953125,
					135.3203125
				],
				[
					-213.96484375,
					135.625
				],
				[
					-210.51171875,
					137.046875
				],
				[
					-198.81640625,
					139.96875
				],
				[
					-157.2421875,
					144.86328125
				],
				[
					-117.0078125,
					147.4453125
				],
				[
					-88.7890625,
					147.4453125
				],
				[
					-82.33203125,
					146.16015625
				],
				[
					-82.02734375,
					145.23828125
				],
				[
					-82.02734375,
					145.23828125
				]
			],
			"pressures": [],
			"simulatePressure": true,
			"lastCommittedPoint": [
				-82.02734375,
				145.23828125
			]
		},
		{
			"id": "gQgSLX3d0UFoI3Z6Bdsk8",
			"type": "image",
			"x": -838.0982484334938,
			"y": 148.26316214037394,
			"width": 899.872679104501,
			"height": 354.32486739739727,
			"angle": 0,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": null,
			"seed": 1006166242,
			"version": 6,
			"versionNonce": 1315923170,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091146,
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
			"id": "rg41A_bHyMBLkEBd_2Qw4",
			"type": "arrow",
			"x": -362.14332229455823,
			"y": 310.83372872241614,
			"width": 367.0319516781522,
			"height": 17.96802460639259,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": {
				"type": 2
			},
			"seed": 855347298,
			"version": 22,
			"versionNonce": 508514878,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091146,
			"link": null,
			"locked": false,
			"points": [
				[
					0,
					0
				],
				[
					367.0319516781522,
					17.96802460639259
				]
			],
			"lastCommittedPoint": null,
			"startBinding": null,
			"endBinding": null,
			"startArrowhead": null,
			"endArrowhead": "arrow"
		},
		{
			"id": "gx5qiXZa",
			"type": "text",
			"x": 399.52071475691935,
			"y": -172.38389454110973,
			"width": 11,
			"height": 25,
			"angle": 0,
			"strokeColor": "#000000",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 1,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": null,
			"seed": 1378763198,
			"version": 4,
			"versionNonce": 783579298,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091146,
			"link": null,
			"locked": false,
			"text": "",
			"rawText": "",
			"fontSize": 20,
			"fontFamily": 1,
			"textAlign": "left",
			"verticalAlign": "top",
			"baseline": 18,
			"containerId": null,
			"originalText": ""
		},
		{
			"id": "SaZ_6jwVn_RoU4JCiol_-",
			"type": "image",
			"x": -461.2436753429747,
			"y": -204.7569493126739,
			"width": 1240.8412167994736,
			"height": 517.0171736664473,
			"angle": 0,
			"strokeColor": "transparent",
			"backgroundColor": "transparent",
			"fillStyle": "hachure",
			"strokeWidth": 2,
			"strokeStyle": "solid",
			"roughness": 0,
			"opacity": 100,
			"groupIds": [],
			"roundness": null,
			"seed": 630703486,
			"version": 22,
			"versionNonce": 1376008226,
			"isDeleted": true,
			"boundElements": null,
			"updated": 1675749091146,
			"link": null,
			"locked": false,
			"status": "pending",
			"fileId": "025c87d987289733bc4dbab89f9ad8fbce531d2a",
			"scale": [
				1,
				1
			]
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
		"currentItemFontFamily": 2,
		"currentItemFontSize": 20,
		"currentItemTextAlign": "left",
		"currentItemStartArrowhead": null,
		"currentItemEndArrowhead": "triangle",
		"scrollX": 872.3902961503412,
		"scrollY": 664.6489296845665,
		"zoom": {
			"value": 0.5714217798886108
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