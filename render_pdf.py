import subprocess
from pathlib import Path


def render_pdf_from_template(company_id: int, restaurant_name: str = "Название ресторана"):
    base_dir = Path(__file__).parent.resolve()
    template_path = base_dir / "template.tex"

    report_dir = base_dir / "files" / str(company_id) / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    output_tex = report_dir / "output.tex"
    output_pdf = report_dir / "output.pdf"

    image_path = base_dir / "images" / str(company_id)
    report_path = base_dir / "files" / str(company_id)

    replacements = {
        "<<SENTIMENT_IMAGE>>": (image_path / "sentiment_donut_chart.png").as_posix(),
        "<<CATEGORY_IMAGE>>": (image_path / "category_donut_chart.png").as_posix(),
        "<<HISTOGRAM_IMAGE>>": (image_path / "histogram.png").as_posix(),
        "<<STAR_IMAGE>>": (image_path / "star_percent_stacked_bar.png").as_posix(),
        "<<HEATMAP_IMAGE>>": (image_path / "heatmap_category_sentiment_rus.png").as_posix(),
        "<<SUMMARY_TEX>>": (report_path / "summary_section.tex").as_posix(),
        "<<EXAMPLES_TEX>>": (report_path / "annotated_examples.tex").as_posix(),
        "<<RESTAURANT_NAME>>": restaurant_name,
        "<<LOGO_IMAGE>>": (base_dir / "images" / "logo.png").as_posix()
    }

    tex = template_path.read_text(encoding="utf-8")
    for key, val in replacements.items():
        tex = tex.replace(key, val)

    output_tex.write_text(tex, encoding="utf-8")

    try:
        subprocess.run(
            ["/Library/TeX/texbin/xelatex", "-interaction=nonstopmode", str(output_tex.name)],
            cwd=report_dir,
            check=True
        )
        print(f"успешно создан: {output_pdf}")
    except subprocess.CalledProcessError as e:
        print("Ошибка", e)

