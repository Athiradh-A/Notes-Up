#set page(
  paper: "a4",
  margin: (top: 20mm, bottom: 18mm, left: 20mm, right: 20mm),
  header: [
    #set text(size: 8.5pt, fill: luma(105))
    #align(right)[Note'sUp — AI Study Guide]
  ],
  footer: [
    #set text(size: 8pt, fill: luma(120))
    #align(center)[#context counter(page).display()]
  ],
)

#set text(
  font: ("Times New Roman", "Liberation Serif", "STIX Two Text", "Noto Serif"),
  size: 10pt,
  lang: "en",
)

#set par(
  justify: true,
  leading: 0.78em,
  spacing: 0.55em,
)

#show heading.where(level: 1): it => {
  set text(size: 17pt, weight: "bold")
  block(above: 0.8em, below: 0.5em)[#it.body]
}

#show heading.where(level: 2): it => {
  set text(size: 12pt, weight: "bold")
  block(above: 0.75em, below: 0.3em)[#it.body]
}

#show heading.where(level: 3): it => {
  set text(size: 10pt, weight: "bold")
  block(above: 0.55em, below: 0.2em)[#it.body]
}

#show list: set list(marker: "•")
#set math.equation(numbering: "(1)")
#show math.equation: set text(size: 10pt)
#show math.equation: set block(spacing: 0.55em)
#show enum: set enum(numbering: "1.")

{{CONTENT}}
