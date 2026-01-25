# Slidev Syntax Rules Guide

Slidev is a presentation tool based on Markdown. Below are its core syntax rules.

## 1. Basic Structure

### Slide Separator
Use `---` (three dashes) to separate slides.

```markdown
# Slide 1

---

# Slide 2
```

### Frontmatter (Metadata)
The document must start with Frontmatter to define global configurations. Each slide (under the separator) can also have Frontmatter to define local configurations for that page.

```markdown
---
layout: cover
background: ./images/bg.png
class: text-center
---
```

## 2. Layouts

Slidev provides various built-in layouts, specified via the `layout` field.

*   **`cover`**: Cover page, usually for the presentation title.
*   **`default`**: Default layout, simple title and content.
*   **`center`**: Content is centered vertically and horizontally.
*   **`intro`**: Intro page, typically title on the left and content on the right.
*   **`two-cols`**: Two-column layout.
    *   Left column content goes after the Frontmatter.
    *   Right column content is separated by `::right::`.
*   **`two-cols-header`**: Two-column layout with a header.
*   **`image-left` / `image-right`**: Image on one side, content on the other. Requires the `image` field to specify the image path.
*   **`full`**: Full-screen content.
*   **`end`**: End page.

Example:

```markdown
---
layout: two-cols
---

# Left Title

Left content...

::right::

# Right Title

Right content...
```

## 3. Text and Styling

### Standard Markdown
Supports all standard Markdown syntax:
*   **Bold**: `**bold**`
*   *Italic*: `*italic*`
*   [Link](https://sli.dev)
*   `Inline code`

### Classes
You can use the `class` field in the frontmatter to add classes to the root element of the slide (Tailwind CSS).

```markdown
---
class: text-center
---
```

### Colors and Backgrounds
*   Text color: `<span class="text-red-500">Red Text</span>`
*   Background color: Set `background` in Frontmatter.

## 4. Special Components and Features

### Animations (Clicks)
Use `v-click` to control element progressive display.

```markdown
<v-click>
This text will appear after a click.
</v-click>

<!-- Or use directive -->
<div v-click>
  Content
</div>
```

List items progressive display:

```markdown
<v-clicks>

- Item 1
- Item 2
- Item 3

</v-clicks>
```

### Code Blocks
Supports syntax highlighting and line numbers.

    ```python {all|1|3-4}
    def hello():
        print("Hello World")
        return True
    ```

### Icons
You can use Iconify icons directly, in the format `<logos-vue />` or `<mdi-account />`.

### Images
```markdown
![Alt text](./image.png)
```
Or use specific positioning:
```markdown
<img src="/image.png" class="absolute top-10 right-10 w-20" />
```
