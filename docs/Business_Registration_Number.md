사업자 인증은 어떤 api를 사용하는가?
입점사 **사업자번호(10자리) 검증**은 보통 토스 같은 PG API가 아니라, **국세청(공공데이터포털) “사업자등록정보 진위확인 및 상태조회” OpenAPI**를 붙여서 합니다. ([데이터.gov.kr][1])

---

## 어떤 API를 쓰나?

### 1) “운영중/폐업 여부만 빠르게” → **상태조회(Status)**

* 엔드포인트: `POST https://api.odcloud.kr/api/nts-businessman/v1/status`
* QueryString: `serviceKey`(필수), `returnType`(선택)
* Body(JSON): `{ "b_no": ["1234567890"] }` 처럼 사업자번호 배열
* 1회 최대 100개까지 조회 가능 ([Postman][2])

### 2) “진짜 그 사업자가 맞는지(대표자/개업일 등까지 매칭)” → **진위확인(Validate)**

* 엔드포인트: `POST https://api.odcloud.kr/api/nts-businessman/v1/validate`
* Body(JSON): `businesses` 배열로 `b_no`, `start_dt`, `p_nm` 등 추가정보 포함 ([Postman][2])

> 실무에선 보통 **1차: status로 폐업/휴업 컷** → (필요하면) **2차: validate로 진위확인** 흐름이 제일 깔끔합니다.

---

## 발급/사용 흐름 (serviceKey 받는 법)

1. 공공데이터포털에서 **“국세청_사업자등록정보 진위확인 및 상태조회 서비스”** 활용신청
2. 승인되면 **일반 인증키(serviceKey)** 발급
3. 호출 시 `serviceKey`를 **URL QueryString**으로 붙여서 사용 ([Postman][2])
   (호출 제한: 1회 100건 / 1일 100만건) ([데이터.gov.kr][1])

---

## 응답에서 뭘 기준으로 “통과/거절”하나?

상태조회 응답에 보통 이런 필드가 옵니다: `b_stt_cd`, `tax_type`, `end_dt` 등 ([Postman][2])

대표적으로 많이 쓰는 컷 기준:

* `b_stt_cd`

  * `01` 계속사업자(정상)
  * `02` 휴업자
  * `03` 폐업자 ([flytodata.com][3])

(정책은 서비스마다 다르지만) 보통은

* **01만 통과**, 02/03은 가입/정산/판매 제한 같은 정책을 걸어요.

---

## Node.js 예시 (status 조회)

```js
import axios from "axios";

const SERVICE_KEY = process.env.DATA_GO_SERVICE_KEY; // 공공데이터포털에서 받은 serviceKey (보통 URL 인코딩 필요)
const url = "https://api.odcloud.kr/api/nts-businessman/v1/status";

export async function checkBizStatus(bizNo10) {
  const bizNo = String(bizNo10).replace(/[^0-9]/g, ""); // 하이픈 제거
  if (bizNo.length !== 10) throw new Error("사업자번호는 10자리여야 합니다.");

  const res = await axios.post(
    `${url}?serviceKey=${encodeURIComponent(SERVICE_KEY)}&returnType=JSON`,
    { b_no: [bizNo] },
    { headers: { "Content-Type": "application/json" } }
  );

  const item = res.data?.data?.[0];
  // item.b_stt_cd: 01/02/03
  return item;
}
```

---
reference: 
[1]: https://www.data.go.kr/data/15081808/openapi.do?utm_source=chatgpt.com "국세청_사업자등록정보 진위확인 및 상태조회 서비스 | 공공데이터포털"
[2]: https://www.postman.com/planetary-moon-750577/seocheck-api/documentation/dcliwd8/ "국세청_사업자등록정보 진위확인 및 상태조회 서비스 | Documentation | Postman API Network"
[3]: https://www.flytodata.com/reference-business?utm_source=chatgpt.com "플라이투데이터 - Reference Business"
