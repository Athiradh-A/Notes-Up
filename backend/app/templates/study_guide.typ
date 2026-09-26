#set page(
  paper: "a4",
  margin: (top: 24mm, bottom: 22mm, left: 22mm, right: 22mm),
  header: [
    #set text(size: 8.5pt, fill: luma(105))
    #align(right)[Note'sUp — AI Study Guide]
  ],
  footer: [
    #set text(size: 8pt, fill: luma(120))
    #align(center)[#counter(page).display()]
  ],
)

#set text(
  font: ("Aptos", "Arial", "Liberation Sans", "Noto Sans"),
  size: 10.5pt,
  lang: "en",
)

#set par(
  justify: false,
  leading: 0.72em,
  spacing: 0.8em,
)

#show heading.where(level: 1): it => {
  set text(size: 19pt, weight: "bold")
  block(above: 1.2em, below: 0.7em)[#it.body]
}

#show heading.where(level: 2): it => {
  set text(size: 14pt, weight: "bold")
  block(above: 1em, below: 0.45em)[#it.body]
}

#show heading.where(level: 3): it => {
  set text(size: 11.5pt, weight: "bold")
  block(above: 0.8em, below: 0.3em)[#it.body]
}

#show list: set list(marker: "•")
#show enum: set enum(numbering: "1.")

{{CONTENT}}
