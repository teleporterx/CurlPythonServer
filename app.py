import os
import re
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
        # Get content length and read the raw POST data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        # Extract boundary from the content type header
        content_type = self.headers['Content-Type']
        boundary = content_type.split("=")[1].encode()  # Get boundary for multipart

        # Split the data into parts based on boundary
        parts = post_data.split(boundary)
        
        for part in parts:
            if b'Content-Disposition' in part:
                # Find the filename
                filename_start = part.find(b'filename="') + len(b'filename="')
                filename_end = part.find(b'"', filename_start)
                if filename_start == -1 or filename_end == -1:
                    continue
                
                filename = part[filename_start:filename_end].decode('utf-8').strip()
                
                # Sanitize the filename to prevent directory traversal attacks
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)  # Replace invalid characters
                if not filename:  # If sanitized filename is empty, skip
                    continue
                
                file_data_start = part.find(b'\r\n\r\n') + 4  # Skip headers
                file_data_end = part.rfind(b'\r\n')  # End of file data
                
                if file_data_start == -1 or file_data_end == -1:
                    continue
                
                file_data = part[file_data_start:file_data_end]

                # Save the file
                if not os.path.exists(UPLOAD_DIRECTORY):
                    os.makedirs(UPLOAD_DIRECTORY)

                output_file_path = os.path.join(UPLOAD_DIRECTORY, filename)
                
                with open(output_file_path, 'wb') as output_file:
                    output_file.write(file_data)

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'File uploaded successfully\n')
                return

        self.send_response(400)
        self.end_headers()
        self.wfile.write(b'Error: No valid file found in upload.')

    def list_uploads(self):
        try:
            if not os.path.exists(UPLOAD_DIRECTORY):
                os.makedirs(UPLOAD_DIRECTORY)
            file_list = os.listdir(UPLOAD_DIRECTORY)
            file_list.sort()
            response = f"""
                <html>
                <head>
                    <title>CurlPythonServer</title>
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
            # Correctly construct the file path by removing '/uploads/' from self.path
            file_name = self.path.split('/')[-1]  # Get only the filename
            file_path = os.path.join(UPLOAD_DIRECTORY, file_name)
            
            print(f"Attempting to serve file at path: {file_path}")  # Debugging output
            
            if not os.path.exists(file_path):
                print(f"File not found at path: {file_path}")  # Debugging output
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
            print(f"Error serving file: {str(e)}")  # Debugging output
            self.send_error(500, str(e))

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandlerWithUpload, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        httpd.server_close()  # Clean up the server
        print("Server stopped.")

# Main
if __name__ == "__main__":
    run()
