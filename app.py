import os
import cgi
from http.server import HTTPServer, BaseHTTPRequestHandler

UPLOAD_DIRECTORY = "./uploads"

TITLE_ASCII = """
▒█▀▀█ █░░█ █▀▀█ █░░ ▒█▀▀█ █░░█ ▀▀█▀▀ █░░█ █▀▀█ █▀▀▄ ▒█▀▀▀█ █▀▀ █▀▀█ ▀█░█▀ █▀▀ █▀▀█ 
▒█░░░ █░░█ █▄▄▀ █░░ ▒█▄▄█ █▄▄█ ░░█░░ █▀▀█ █░░█ █░░█ ░▀▀▀▄▄ █▀▀ █▄▄▀ ░█▄█░ █▀▀ █▄▄▀ 
▒█▄▄█ ░▀▀▀ ▀░▀▀ ▀▀▀ ▒█░░░ ▄▄▄█ ░░▀░░ ▀░░▀ ▀▀▀▀ ▀░░▀ ▒█▄▄▄█ ▀▀▀ ▀░▀▀ ░░▀░░ ▀▀▀ ▀░▀▀
"""

class SimpleHTTPRequestHandlerWithUpload(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.list_uploads()
        elif self.path.startswith('/uploads/'):
            self.serve_file()
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        if ctype == 'multipart/form-data':
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_length = int(self.headers['Content-Length'])
            fs = cgi.FieldStorage(fp=self.rfile,
                                  headers=self.headers,
                                  environ={'REQUEST_METHOD': 'POST'},
                                  keep_blank_values=True)

            if 'file' not in fs or not fs['file'].filename:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Error: No file chosen for upload. Please choose a file and try again.')
                return

            file_item = fs['file']
            filename = os.path.basename(file_item.filename)
            file_data = file_item.file.read()

            if not file_data:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Error: No file content. Please choose a file with content and try again.')
                return

            if not os.path.exists(UPLOAD_DIRECTORY):
                os.makedirs(UPLOAD_DIRECTORY)
            with open(os.path.join(UPLOAD_DIRECTORY, filename), 'wb') as output_file:
                output_file.write(file_data)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'File uploaded successfully\n')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Bad request')

    def list_uploads(self):
        try:
            if not os.path.exists(UPLOAD_DIRECTORY):
                os.makedirs(UPLOAD_DIRECTORY)
            file_list = os.listdir(UPLOAD_DIRECTORY)
            file_list.sort()
            response = f"""
                <html>
                <head>
                    <title>CurlSerpentServer</title>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1 {{ white-space: pre; font-family: monospace; }}
                        h2 {{ color: #4CAF50; }}
                        ul {{ list-style-type: none; padding: 0; }}
                        li {{ margin: 5px 0; }}
                        a {{ text-decoration: none; color: #333; }}
                        a:hover {{ text-decoration: underline; }}
                        form {{ margin-top: 20px; }}
                        input[type="file"] {{ margin: 10px 0; }}
                        input[type="submit"] {{
                            background-color: #4CAF50;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            text-align: center;
                            text-decoration: none;
                            display: inline-block;
                            font-size: 16px;
                            margin: 4px 2px;
                            cursor: pointer;
                            border-radius: 4px;
                        }}
                        .error {{ color: red; }}
                        .cli-instructions {{ margin-top: 20px; }}
                        .cli-instructions code {{ background-color: #f1f1f1; padding: 2px 4px; }}
                    </style>
                </head>
                <body>
                    <h1>{TITLE_ASCII}</h1>
                    <h2>Uploaded Files</h2>
                    <ul>
            """
            for file_name in file_list:
                file_path = os.path.join(UPLOAD_DIRECTORY, file_name)
                response += f'<li><a href="/uploads/{file_name}">{file_name}</a></li>'
            response += """
                    </ul>
                    <h2>Upload a New File</h2>
                    <form enctype="multipart/form-data" action="/" method="post">
                        <input type="file" name="file">
                        <input type="submit" value="Upload File">
                    </form>
                    <div class="cli-instructions">
                        <h2>CLI Manual File Upload</h2>
                        <p>To upload a file via the command line, use the following <code>curl</code> command:</p>
                        <code>curl -F 'file=@path_to_your_file' http://localhost:8000</code>
                    </div>
                </body>
                </html>
            """
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            self.send_error(500, str(e))

    def serve_file(self):
        try:
            file_path = self.path[1:]  # remove leading '/'
            if not os.path.exists(file_path):
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'File not found')
                return
            
            with open(file_path, 'rb') as file:
                self.send_response(200)
                self.send_header("Content-Type", 'application/octet-stream')
                self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(file_path)}"')
                self.end_headers()
                self.wfile.write(file.read())
        except Exception as e:
            self.send_error(500, str(e))

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandlerWithUpload, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}')
    httpd.serve_forever()

#main
if __name__ == "__main__":
    run()
