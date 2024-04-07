def add_css_classes_to_form_fields(form, css_classes):
    for field in form.fields:
        form.fields[field].widget.attrs['class'] = css_classes
    return form