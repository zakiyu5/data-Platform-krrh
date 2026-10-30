from app import create_app

app = create_app()

if __name__ == "__main__":
    print("\\n  KRRH Platform running at http://127.0.0.1:5000\\n")
    app.run(debug=True, host="127.0.0.1", port=8800)
