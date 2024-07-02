# import io

# import numpy as np
# from PIL import Image

# from api.db import LLMType
# from api.db.services.llm_service import LLMBundle
# from rag.nlp import tokenize
# from deepdoc.vision import OCR

# ocr = OCR()


# def chunk(filename, binary, tenant_id, lang, callback=None, **kwargs):
#     try:
#         cv_mdl = LLMBundle(tenant_id, LLMType.IMAGE2TEXT, lang=lang)
#     except Exception as e:
#         callback(prog=-1, msg=str(e))
#         return []
#     img = Image.open(io.BytesIO(binary)).convert('RGB')
#     doc = {
#         "docnm_kwd": filename,
#         "image": img
#     }
#     bxs = ocr(np.array(img))
#     txt = "\n".join([t[0] for _, t in bxs if t[0]])
#     eng = lang.lower() == "english"
#     callback(0.4, "Finish OCR: (%s ...)" % txt[:12])
#     if (eng and len(txt.split(" ")) > 32) or len(txt) > 32:
#         tokenize(doc, txt, eng)
#         callback(0.8, "OCR results is too long to use CV LLM.")
#         return [doc]

#     try:
#         callback(0.4, "Use CV LLM to describe the picture.")
#         ans = cv_mdl.describe(binary)
#         callback(0.8, "CV LLM respoond: %s ..." % ans[:32])
#         txt += "\n" + ans
#         tokenize(doc, txt, eng)
#         return [doc]
#     except Exception as e:
#         callback(prog=-1, msg=str(e))

#     return []
