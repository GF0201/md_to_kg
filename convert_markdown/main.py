from converter import batch_convert_pdfs

if __name__ == "__main__":
    input_folder = "./extracted_pdfs"
    output_folder = "./mds"
    batch_convert_pdfs(input_folder, output_folder)
