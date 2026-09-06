"""Tests for the lightweight Markdown → HTML renderer used in output windows."""

from jhora.ui.richtext import md_document, md_to_html


class TestMarkdownRenderer:
    def test_bold(self):
        assert "<b>Rahu</b>" in md_to_html("Hi **Rahu** here")

    def test_italic(self):
        assert "<i>works</i>" in md_to_html("It *works* well")

    def test_header(self):
        assert "<h2" in md_to_html("## Vimsottari Dasa")

    def test_inline_code(self):
        html = md_to_html("Run `jhora chart` now")
        assert "<code" in html
        assert "jhora chart" in html

    def test_code_block(self):
        html = md_to_html("```bash\njhora ai --provider lmstudio\n```")
        assert "<pre" in html
        assert "jhora ai --provider lmstudio" in html

    def test_unordered_list(self):
        html = md_to_html("- one\n- two")
        assert "<ul" in html
        assert "<li" in html and "one" in html and "two" in html

    def test_ordered_list(self):
        html = md_to_html("1. first\n2. second")
        assert "<ol" in html
        assert "<li" in html and "first" in html

    def test_table_with_separator(self):
        rows = "| Planet | Sign |\n|--------|------|\n| Moon | Cancer |"
        html = md_to_html(rows)
        assert "<table" in html
        assert "<th" in html and "Planet" in html
        assert "<td" in html and "Moon" in html

    def test_blockquote(self):
        html = md_to_html("> Shloka from Brihat Parashara Hora Shastra")
        assert "<blockquote" in html

    def test_hr(self):
        assert "<hr" in md_to_html("---")

    def test_link(self):
        html = md_to_html("[BPHS](https://example.com)")
        assert '<a href="https://example.com">BPHS</a>' in html

    def test_escapes_html(self):
        html = md_to_html("Moon < Sun & Rahu > Nobody")
        assert "&lt;" in html
        assert "&amp;" in html

    def test_paragraph_break(self):
        html = md_to_html("First line\nsecond line\n\nNext paragraph")
        assert "First line<br>second line" in html
        assert "Next paragraph" in html

    def test_document_wrapper(self):
        doc = md_document("**bold**", size_px=15)
        assert "font-size:15px" in doc
        assert "<b>bold</b>" in doc

    def test_empty(self):
        assert md_to_html("") == ""
        assert md_to_html("   \n  ") == ""