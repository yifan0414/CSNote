<%*
let url = 'https://www.tianqi.com/heze/'
let res = await request({url: url,method: "GET"});
res = res.replace(/\s/g,'')
r=/<ddclass="weather">[\s\S]*?<\/dd>/g
let data = r.exec(res)[0]
r = /<span><b>(.*?)<\/b>(.*?)<\/span>/g
data = r.exec(data)
let weather='菏泽'+data[2]+data[1]
if (data[1]=='晴') weather=weather+'🔆';
else if (data[1]=='阴') weather=weather+'☁️';
-%>
<% weather %>