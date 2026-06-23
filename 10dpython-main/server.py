import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SignLens NLP Server")


class SpeechInput(BaseModel):
    text: str


# TỪ ĐIỂN THÔNG MINH: Nơi cấu hình luật nhảy câu của bạn
TU_DIEN_ANH_XA = {
    "tôi ăn": "tôi đang ăn cơm",
    "tôi học": "tôi đang học bài",
    "tôi đi": "tôi đang đi học",
    "xin chao": "xin chào tất cả mọi người"
}


@app.post("/api/mo-rong-cau")
async def xu_ly_mo_rong_cau(data: SpeechInput):
    # Chuyển về chữ thường để so khớp chính xác
    cau_goc = data.text.strip().lower()

    # Lấy câu đã mở rộng, nếu không có thì trả về câu gốc
    cau_mo_rong = TU_DIEN_ANH_XA.get(cau_goc, data.text)

    return {
        "status": "success",
        "expanded_text": cau_mo_rong
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)