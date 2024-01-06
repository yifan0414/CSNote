---
citekey: {{citekey}}
authors: {{authors}}
title: "{{title | safe}}"
alias: {% if ShortTitle %}"{{shortTitle | safe}}"{% endif %}
Year: {{date | format("YYYY")}}
tags: [literature-note, {% for t in tags %}{{t.tag}}{% if not loop.last %}, {% endif %}{% endfor %}]
Authors: {{authors}}{{directors}}
publisher: "{{publicationTitle}}"
doi: {{DOI}}
---
{#- These can be changed -#}
{#- This is the order in which the annotations are ordered -#}
{%-
   set categoryHeading = {
		"orange":  "Main ideas and conclusions",
        "yellow":  "Ordinary notes",
		"blue":    "Quote / quotable",
		"green":   "Important To Me",
		"red":     "Disagree With Author",
        "purple":  "Interesting side-point",
        "magenta": "Methodology",
		"grey":    "Definitions and concepts"
   }
-%}
{%-
    set categoryIcon = {
        "orange": "💡",
        "yellow": "📚",
        "blue": "💬",
        "green": "💚",
        "red": "⛔",
        "purple": "💭",
        "magenta": "⚙️",
        "grey": "🧩"
    }
-%}
{#- ---------- Don't make any changes under here --------- #}
{%- macro minEditDate() -%}
   {%- set tempDate = "" -%}
	{%- for a in annotations -%}
		{%- set testDate = a.date | format("YYYY-MM-DD#HH:mm:ss") -%}
		{%- if testDate < tempDate or tempDate == ""-%}
			{%- set tempDate = testDate -%}
		{%- endif -%}
	{%- endfor -%}
    {%- for a in notes -%}
		{%- set testDate = a.dateModified | format("YYYY-MM-DD#HH:mm:ss") -%}
		{%- if testDate < tempDate or tempDate == ""-%}
			{%- set tempDate = testDate -%}
		{%- endif -%}
	{%- endfor -%}
	{{tempDate }}
{%- endmacro -%}
{# infer latest note date #}
{%- macro maxEditDate() -%}
   {%- set tempDate = "" -%}
	{%- for n in annotations -%}
		{%- set testDate = n.date | format("YYYY-MM-DD#HH:mm:ss") -%}
		{%- if testDate > tempDate or tempDate == ""-%}
			{%- set tempDate = testDate -%}
		{%- endif -%}
	{%- endfor -%}
	{%- for n in notes -%}
		{%- set testDate = n.dateModified | format("YYYY-MM-DD#HH:mm:ss") -%}
		{%- if testDate > tempDate or tempDate == ""-%}
			{%- set tempDate = testDate -%}
		{%- endif -%}
	{%- endfor -%}
	{{tempDate}}
{%- endmacro -%}
{#- handle | characters in zotero strings used in MD -#}
{% macro formatCell(cellText) -%}
{{ cellText | replace("|","❕")}}
{%- endmacro %}
{#- TAGS: handle space characters in zotero tags -#}
{%- set space = joiner(' ') -%} 
{%- macro printTags(rawTags) -%}
	{%- if rawTags.length > 0 -%}
		{%- for tag in rawTags -%}
			#{{ tag.tag | lower | replace(" ","_") }} {{ space() }} 
		{%- endfor -%}
	{%- endif -%}
{%- endmacro %}
{%-
    set zoteroColors = {
        "#ff6666": "red",
        "#f19837": "orange",
        "#5fb236": "green",
        "#ffd400": "yellow",
        "#2ea8e5": "blue",
        "#a28ae5": "purple",
        "#e56eee": "magenta",
        "#aaaaaa": "grey"
    }
%}
# {{title}}

> [!info]+ Info - [**Zotero**]({{desktopURI}}) {% if DOI %}| [**DOI**](https://doi.org/{{DOI}}){% endif %}  | Local {% for attachment in attachments | filterby("path", "endswith", ".pdf") %}[**PDF**](file:///{{attachment.path | replace(" ", "%20")}}){%- endfor %}
{% if ShortTitle %}> Short title: {{shortTitle | safe}}{% endif -%}
> Authors: {% for c in creators %}[[{{c.firstName}} {{c.lastName}}]], {% endfor %} 
{% if publicationTitle %}> Publication: {{publicationTitle | safe}}{% endif -%}
> Type: {{itemType}}
> Year: {{date | format("YYYY")}}
> Zotero links: [Item]({{select}}) {% if pdfZoteroLink %}PDF: {{pdfZoteroLink}}{% endif %} 
> Web links: {% if itemType == "webpage" %}[{{title}}]({{url}}){%else%}[Item]({{uri}}){%endif%} {% if pdfLink %}PDF: {{pdfLink}}{% endif %} 
> {{printTags(note.tags)}}
>
> **History**
> Date item added to Zotero: [[{{dateAdded | format("YYYY-MM-DD")}}]]
> First date annotations or notes modified: [[{{minEditDate() | truncate(10,true,"")}}]]
> Last date annotations or notes modified: [[{{maxEditDate()| truncate(10,true,"")}}]]

{%- if relations.length > 0 %}
{{ "" }}
> [!abstract] Related Zotero items ({{ relations.length}}):  
>
> | title | proxy note | desktopURI |
> | --- | --- | --- |
{%- for r in relations %}
> | {{formatCell(r.title)}} | [[@{{r.citekey}}]] | [Zotero Link]({{r.desktopURI}}) | {% if rel.DOI %}> DOI: {{rel.DOI}}{% endif %} |
{%- endfor -%}
{{ "" }}
{%- endif %}

> [!abstract]+
> {% if abstractNote %}
> {{abstractNote|replace("\n"," ")}}
> {% endif %}

{% if notes.length > 0 %}
> [!note] Notes ({{notes.length}})
{{ "" }}
{%- for note in notes -%}
{#- Clean up note, change heading level, just in case -#}
> {{ note.note | replace ("# ","### ") }}
> {%- if note.imageBaseName %}>![[Paper/Note/{{citekey}}/{{entry.imageBaseName}}]]<br>{% endif -%}
> {{printTags(note.tags)}}
> <small>📝️ (modified: {{ note.dateModified | format("YYYY-MM-DD") }}) [link](zotero://select/library/items/{{note.key}}) - [web]({{note.uri}})</small>
>  {{ "" }}
> ---
{% endfor %}
{% endif -%}



---
## Persistant notes 
{% persist "notes" %}

{% endpersist %}

---
# Annotations <small>(Exported: [[{{exportDate | format("YYYY-MM-DD")}}]]</small>)

{% for color, colorCategorie in zoteroColors %}
{%- for entry in annotations | filterby ("color", "startswith", color) -%}
{%- if entry.id %}
{%- if entry and loop.first %}## {{categoryIcon[zoteroColors[entry.color]]}} {{categoryHeading[zoteroColors[color]]}}
{% endif -%}
{%- if entry.annotatedText %}{{categoryIcon[zoteroColors[entry.color]]}} {{entry.annotatedText}}
{% endif -%} 
{%- if entry.imageBaseName %}>![[Paper/Note/{{citekey}}/{{entry.imageBaseName}}]]<br>
{%- endif %}
{%- if entry.comment %}📝️ {{entry.comment}}
{% endif -%}
{{printTags(entry.tags)}} <small>([page-{{entry.pageLabel}}](zotero://open-pdf/library/items/{{entry.attachment.itemKey}}?page={{entry.pageLabel}}&annotation={{entry.id}})) edited:[[{{ entry.date | format("YYYY-MM-DD")}}]]</small> ^{{ entry.id | lower }}

{% endif -%}
{% endfor -%}
{% endfor -%}