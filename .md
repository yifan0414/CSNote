```dataviewjs
const files = app.vault.getMarkdownFiles()
const prompt = "<% tp.system.prompt("Query for") %>"

const fileObject = files.map(async (file) => {
const fileLink = "[["+file.name.split(".")[0]+"]]"
const content = await app.vault.cachedRead(file)
return {fileLink, content}
})

Promise.all(fileObject).then(files => {

let values = new Set(files.reduce((acc, file) => {
const lines = file.content.split("\n").filter(line => line.match(new RegExp(prompt, "i")))
if (lines[0] && !file.fileLink.includes("<% tp.file.title %>")) {
if (acc[0]) {
return [...acc, [file.fileLink, lines.join("\n")]]
} else {
return [[file.fileLink, lines.join("\n")]]
}
}
return acc
}, []))

dv.header(1, prompt)
dv.table(["file", "lines"], Array.from(values))

})
```