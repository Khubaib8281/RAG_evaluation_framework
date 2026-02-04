try:
    # new package split
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    # fallback for older versions
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
def chunk_text(text: str, chunk_size=2000, overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)
