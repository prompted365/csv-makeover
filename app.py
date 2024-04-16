
from flask import Flask, request, render_template, send_file
import pandas as pd
import json
import xml.etree.ElementTree as ET
import yaml
import os
from io import BytesIO

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        output_format = request.form['format']
        if file and output_format:
            data = pd.read_csv(file)
            if output_format == 'json':
                response = data.to_json(orient='records', indent=2)
                filename = 'output.json'
                mimetype = 'application/json'
            elif output_format == 'xml':
                response = df_to_xml(data)
                filename = 'output.xml'
                mimetype = 'application/xml'
            elif output_format == 'yaml':
                response = yaml.dump(json.loads(data.to_json(orient='records')), allow_unicode=True)
                filename = 'output.yaml'
                mimetype = 'application/x-yaml'
            else:
                return "Unsupported format", 400

            buffer = BytesIO()
            buffer.write(response.encode())
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)

    return render_template('index.html')

def df_to_xml(df):
    root = ET.Element("root")
    for _, row in df.iterrows():
        record = ET.SubElement(root, "record")
        for field, value in row.items():
            ET.SubElement(record, field).text = str(value)
    return ET.tostring(root, encoding='unicode', method='xml')

@app.route('/view-json', methods=['POST'])
def view_json():
    file = request.files['file']
    if file:
        data = pd.read_csv(file)
        response = data.to_json(orient='records', indent=2)
        return "<pre>" + response + "</pre>"
    return "No file provided", 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
