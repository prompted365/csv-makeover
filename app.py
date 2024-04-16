from flask import Flask, request, render_template, send_file, jsonify
import pandas as pd
import json
import xml.etree.ElementTree as ET
import yaml
import os
from io import BytesIO

app = Flask(__name__)

@app.route('/view-data', methods=['POST'])
def view_data():
    file = request.files['file']
    output_format = request.form['format']
    if file and output_format:
        # Determine file type and read data accordingly
        if file.filename.endswith('.csv'):
            data = pd.read_csv(file)
        elif file.filename.endswith('.xlsx'):
            data = pd.read_excel(file)
        else:
            return "Unsupported file format", 400

        # Convert data to selected format
        converted_data, _, _ = convert_to_format(data, output_format)
        
        # Prepare the original and converted data for display
        original_data = data.to_csv(index=False)
        original_pretty = jsonify(data.to_dict(orient='records'))
        
        if output_format in ['json', 'yaml', 'xml']:
            raw_view = converted_data
            pretty_view = json.dumps(json.loads(converted_data), indent=2) if output_format != 'xml' else converted_data
        else:
            # Handling non-text based formats for preview (e.g., Excel can't be previewed as text)
            raw_view = "Binary content - download to view"
            pretty_view = "Binary content - download to view"

        return render_template('view_data.html', original_data=original_data, original_pretty=original_pretty,
                               raw_view=raw_view, pretty_view=pretty_view, filename=file.filename)
    return "No file provided", 400

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        output_format = request.form['format']
        if file and output_format:
            data = pd.read_csv(file)
            response, filename, mimetype = convert_to_format(data, output_format)
            if response:
                buffer = BytesIO()
                if isinstance(response, bytes):
                    buffer.write(response)
                else:
                    buffer.write(response.encode())
                buffer.seek(0)
                return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)
            else:
                return "Unsupported format", 400
    return render_template('index.html')

def convert_to_format(data, format):
    if format == 'json':
        response = data.to_json(orient='records', indent=2)
        return response, 'output.json', 'application/json'
    elif format == 'xml':
        response = df_to_xml(data)
        return response, 'output.xml', 'application/xml'
    elif format == 'yaml':
        response = yaml.dump(json.loads(data.to_json(orient='records')), allow_unicode=True)
        return response, 'output.yaml', 'application/x-yaml'
    elif format == 'excel':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        data.to_excel(writer, index=False)
        writer.save()
        output.seek(0)
        return output.getvalue(), 'output.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return None, None, None

def df_to_xml(df):
    root = ET.Element("Data")
    for _, row in df.iterrows():
        record = ET.SubElement(root, "Record")
        for field, value in row.items():
            ET.SubElement(record, field).text = str(value)
    return ET.tostring(root, encoding='unicode', method='xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)