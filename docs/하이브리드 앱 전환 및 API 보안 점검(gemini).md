# **하이브리드 모바일 애플리케이션 전환 및 API 보안 고도화 상세 설계 명세서**

본 문서는 웹 기반 프로젝트를 iOS 및 Android 하이브리드 앱으로 전환하고, 실제 스토어 출시를 위한 패키징 절차 및 API 보안 취약점 점검을 자동화하기 위한 기술적 가이드를 제공합니다. 특히 AI 코딩 어시스턴트인 Claude Code를 활용한 보안 감사 체계 구축에 중점을 둡니다.

## **1\. 하이브리드 프레임워크 선정 및 아키텍처**

기존 웹 코드의 재사용성을 극대화하면서 네이티브 성능을 확보하기 위해 Capacitor 또는 React Native를 선택합니다. 1

### **1.1 프레임워크 기술 비교**

| 항목 | Capacitor | React Native |
| :---- | :---- | :---- |
| **렌더링 방식** | 시스템 WebView | 네이티브 UI 컴포넌트 |
| **웹 코드 재사용** | 100% 가능 (프레임워크 무관) | 70-90% (별도 UI 작성 필요) |
| **네이티브 접근** | 직접 API 접근 (No Bridge) | Bridge 기반 통신 |
| **학습 곡선** | 낮음 (기존 웹 기술 활용) | 보통 (React 지식 필요) |

3

### **1.2 아키텍처 전략**

* **웹 앱 통합:** Capacitor를 사용하여 웹 소스를 래핑하고, 고성능 애니메이션이 필요한 특정 모듈에 대해서만 네이티브 플러그인을 개발합니다. 4  
* **성능 최적화:** 앱 시작 시간(Startup Time) 단축을 위해 번들 크기를 최소화하고, 무거운 연산은 네이티브 레이어에서 처리하도록 설계합니다. 3

## **2\. 플랫폼별 패키징 및 스토어 출시 요건**

스토어 출시를 위해서는 각 OS가 요구하는 코드 서명(Code Signing) 및 바이너리 최적화 기준을 준수해야 합니다. 6

### **2.1 iOS 패키징 (Apple App Store)**

* **필수 자산:** 개발자 계정($99/년), 배포용 인증서(Distribution Certificate), 프로비저닝 프로파일. 8  
* **보안 요구사항:** 모든 통신에 HTTPS(TLS 1.2+) 강제, App Transport Security(ATS) 설정. 7  
* **기술 제약:** arm64 아키텍처 지원 필수, 200MB 초과 시 셀룰러 다운로드 제한 주의. 7

### **2.2 Android 패키징 (Google Play Store)**

* **서명 방식:** Play 앱 서명(Google Play App Signing) 권장. 8  
* **키스토어(Keystore) 관리:** 업로드 키와 앱 서명 키 분리 관리. 키스토어 분실 시 업데이트 불가하므로 보안 저장 필수. 6  
* **배포 형식:** APK 대신 효율적인 용량 관리를 위해 Android App Bundle(.aab) 형식을 사용합니다. 7

## **3\. OWASP API Security Top 10 (2023) 기반 보안 점검**

하이브리드 앱의 보안은 데이터를 주고받는 API 엔드포인트의 견고함에서 시작됩니다. 11

### **3.1 핵심 취약점 점검 리스트**

* **API1:2023 (BOLA):** 모든 객체 접근 시 세션의 사용자와 데이터 소유권을 서버 측에서 반드시 검증합니다. 13  
* **API2:2023 (Broken Authentication):** JWT 사용 시 서명 알고리즘(RS256 권장) 검증, 짧은 만료 시간 및 토큰 로테이션을 적용합니다. 13  
* **API3:2023 (BOPLA):** 응답 데이터에서 불필요한 필드를 필터링하고, Mass Assignment를 방지하기 위해 허용된 필드만 입력받는 Allowlist 스키마를 사용합니다. 13  
* **API4:2023 (Unrestricted Resource Consumption):** API 게이트웨이 또는 서버 수준에서 Rate Limiting, 페이로드 크기 제한을 적용합니다. 13  
* **API7:2023 (SSRF):** 사용자 입력 URL을 통한 서버 내부 자원 접근을 차단하고, 외부 도메인에 대한 허용 목록을 관리합니다. 14

13

## **4\. 모바일 특화 보안 기술 구현**

### **4.1 SSL 피닝 (SSL Pinning)**

중간자 공격(MITM) 방지를 위해 앱 내부에 서버 인증서의 공개 키 해시(SHA256 지문)를 포함하여 검증합니다. 16

* **Capacitor:** Capacitor-SSL-Pinning 플러그인 활용. 19  
* **React Native:** react-native-ssl-pinning 또는 react-native-ssl-public-key-pinning 라이브러리 활용. 17

### **4.2 보안 저장소 (Secure Storage)**

인증 토큰 및 민감한 정보는 localStorage 대신 OS의 보안 영역을 사용합니다. 23

* **iOS:** Keychain 활용. 6  
* **Android:** Keystore 기반 EncryptedSharedPreferences 활용. 26

## **5\. Claude Code 연동을 위한 상세 설계 명세**

Claude Code가 프로젝트의 맥락을 이해하고 자동으로 보안 감사를 수행하도록 하기 위한 설정입니다. 28

### **5.1 CLAUDE.md 가이드라인**

프로젝트 루트에 위치하며, Claude Code의 세션 메모리 역할을 합니다. 30

# **프로젝트 아키텍처 및 보안 표준**

## **기술 스택**

* 하이브리드 엔진: Capacitor (iOS/Android)  
* 프론트엔드: React \+ Vite  
* API: Node.js Express \+ JWT (RS256 서명)

## **보안 요구사항 (OWASP API Top 10 준수)**

* 모든 API 응답은 Zod 스키마를 통해 필요한 필드만 노출한다.  
* 로컬 저장은 반드시 capacitor-secure-storage-plugin을 사용한다.  
* HTTPS 통신 시 SSL Pinning 플러그인을 필수 적용한다.

## **주요 명령어**

* 빌드: npm run build  
* 네이티브 동기화: npx cap sync  
* 보안 스캔: npm run security:scan

19

### **5.2 보안 자동화 Hooks (.claude/settings.json)**

도구 실행 전후에 보안 검사를 수행하도록 설정합니다. 33

JSON

{  
  "hooks": {  
    "PreToolUse": \[  
      {  
        "matcher": "Edit",  
        "hooks": \[  
          {  
            "type": "command",  
            "command": "./scripts/secret-leak-check.sh",  
            "statusMessage": "코드 내 민감 정보 유출 검사 중..."  
          }  
        \]  
      }  
    \],  
    "PostToolUse":  
      }  
    \]  
  }  
}

33

### **5.3 커스텀 Skills 정의 (/package-release)**

릴리스 전 보안 감사와 패키징을 통합한 명령어입니다. 29

* **이름:** package-release  
* **설명:** 보안 감사 완료 후 스토어 배포용 바이너리를 생성합니다.  
* **워크플로우:**  
  1. 전체 코드베이스에 대한 OWASP API Security 2023 취약점 스캔을 실행한다. 35  
  2. npm audit을 통해 의존성 보안 이슈를 확인한다. 35  
  3. 플랫폼별(iOS/Android) 코드 서명 자산의 유효성을 검증한다. 6  
  4. 보안 통과 시 npx cap build 명령을 통해 바이너리를 생성한다. 29

6

#### **참고 자료**

1. Capacitor vs React Native: Complete Comparison 2025 \- NextNative, 2월 28, 2026에 액세스, [https://nextnative.dev/comparisons/capacitor-vs-react-native](https://nextnative.dev/comparisons/capacitor-vs-react-native)  
2. Capacitor vs React Native (2025): Which Is Better for Your App? \- NextNative, 2월 28, 2026에 액세스, [https://nextnative.dev/blog/capacitor-vs-react-native](https://nextnative.dev/blog/capacitor-vs-react-native)  
3. Comparing React Native vs Capacitor \- Capgo, 2월 28, 2026에 액세스, [https://capgo.app/blog/comparing-react-native-vs-capacitor/](https://capgo.app/blog/comparing-react-native-vs-capacitor/)  
4. React Native vs. NativeScript vs. Capacitor: Understanding the Tradeoffs \- Appisto, 2월 28, 2026에 액세스, [https://appisto.app/blog/react-native-vs-nativescript-vs-capacitor](https://appisto.app/blog/react-native-vs-nativescript-vs-capacitor)  
5. Flutter vs. React Native vs. Capacitor JS: Choosing the Best Cross-Platform Framework | by Sree Rag E S | Medium, 2월 28, 2026에 액세스, [https://medium.com/@dev.sreerages/flutter-vs-react-native-vs-capacitor-js-choosing-the-best-cross-platform-framework-84ba8ef497b6](https://medium.com/@dev.sreerages/flutter-vs-react-native-vs-capacitor-js-choosing-the-best-cross-platform-framework-84ba8ef497b6)  
6. How to Configure App Signing for iOS and Android in React Native, 2월 28, 2026에 액세스, [https://oneuptime.com/blog/post/2026-01-15-react-native-app-signing/view](https://oneuptime.com/blog/post/2026-01-15-react-native-app-signing/view)  
7. What Binary Requirements Must Your App Meet for Approval?, 2월 28, 2026에 액세스, [https://thisisglance.com/learning-centre/what-binary-requirements-must-your-app-meet-for-approval](https://thisisglance.com/learning-centre/what-binary-requirements-must-your-app-meet-for-approval)  
8. App Signing Explained : Keystores, Certificates, and Provisioning Profiles, 2월 28, 2026에 액세스, [https://dev.to/ersuman/app-signing-explained-keystores-certificates-and-provisioning-profiles-4llh](https://dev.to/ersuman/app-signing-explained-keystores-certificates-and-provisioning-profiles-4llh)  
9. Complete iOS App Setup Guide: From Bundle ID to App Store Submission \- Medium, 2월 28, 2026에 액세스, [https://medium.com/@chandangupta86/complete-ios-app-setup-guide-from-bundle-id-to-app-store-submission-eab1f3d6ce3c](https://medium.com/@chandangupta86/complete-ios-app-setup-guide-from-bundle-id-to-app-store-submission-eab1f3d6ce3c)  
10. SSL Pinning for Capacitor Apps \- Capgo, 2월 28, 2026에 액세스, [https://capgo.app/blog/ssl-pinning-for-capacitor-apps/](https://capgo.app/blog/ssl-pinning-for-capacitor-apps/)  
11. OWASP TOP 10: API security checklist for 2023 \- Escape, 2월 28, 2026에 액세스, [https://escape.tech/blog/owasp-api-security-checklist-for-2023/](https://escape.tech/blog/owasp-api-security-checklist-for-2023/)  
12. OWASP API Security Top 10 Risks \- Wiz, 2월 28, 2026에 액세스, [https://www.wiz.io/academy/api-security/owasp-api-security](https://www.wiz.io/academy/api-security/owasp-api-security)  
13. OWASP Top 10 API Security Risks – 2023, 2월 28, 2026에 액세스, [https://owasp.org/API-Security/editions/2023/en/0x11-t10/](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)  
14. The OWASP API Security Top 10 (2023): A Practical, Actionable Guide for Security Teams, 2월 28, 2026에 액세스, [https://www.sitewall.net/owasp-api-security-top-10-2023/](https://www.sitewall.net/owasp-api-security-top-10-2023/)  
15. OWASP API Security Project, 2월 28, 2026에 액세스, [https://owasp.org/www-project-api-security/](https://owasp.org/www-project-api-security/)  
16. How to Implement SSL Pinning in React Native \- OneUptime, 2월 28, 2026에 액세스, [https://oneuptime.com/blog/post/2026-01-15-react-native-ssl-pinning/view](https://oneuptime.com/blog/post/2026-01-15-react-native-ssl-pinning/view)  
17. Keeping Your React Native App Secure: SSL Pinning and Data Encryption Made Simple | by iyiola osuagwu | Medium, 2월 28, 2026에 액세스, [https://medium.com/@iyiolaosuagwu/keeping-your-react-native-app-secure-ssl-pinning-and-data-encryption-made-simple-4205e0ad67ee](https://medium.com/@iyiolaosuagwu/keeping-your-react-native-app-secure-ssl-pinning-and-data-encryption-made-simple-4205e0ad67ee)  
18. Security Best Practices (SSL Pinning, Data Encryption) in React Native Projects \- Medium, 2월 28, 2026에 액세스, [https://medium.com/@tusharkumar27864/security-best-practices-ssl-pinning-data-encryption-in-react-native-projects-36a6a56fef3b](https://medium.com/@tusharkumar27864/security-best-practices-ssl-pinning-data-encryption-in-react-native-projects-36a6a56fef3b)  
19. mchl18/Capacitor-SSL-Pinning: Ionic Capacitor Plugin to perform SSL checking/pinning. \- GitHub, 2월 28, 2026에 액세스, [https://github.com/mchl18/Capacitor-SSL-Pinning](https://github.com/mchl18/Capacitor-SSL-Pinning)  
20. SSL Pinning Implementation: Tools and Plugins \- Capgo, 2월 28, 2026에 액세스, [https://capgo.app/blog/ssl-pinning-implementation-tools-and-plugins/](https://capgo.app/blog/ssl-pinning-implementation-tools-and-plugins/)  
21. SSL Pinning in React Native Apps — A Beginner-Friendly Guide | by pyTuner | Medium, 2월 28, 2026에 액세스, [https://medium.com/@tejasdabholkarv/ssl-pinning-in-react-native-apps-a-beginner-friendly-guide-bf2e71373743](https://medium.com/@tejasdabholkarv/ssl-pinning-in-react-native-apps-a-beginner-friendly-guide-bf2e71373743)  
22. MaxToyberman/react-native-ssl-pinning \- GitHub, 2월 28, 2026에 액세스, [https://github.com/MaxToyberman/react-native-ssl-pinning](https://github.com/MaxToyberman/react-native-ssl-pinning)  
23. Developer Guide to the 2023 OWASP Top 10 for API Security | OpenText, 2월 28, 2026에 액세스, [https://www.opentext.com/media/white-paper/developer-guide-to-the-2023-owasp-top-10-for-api-security-wp-en.pdf](https://www.opentext.com/media/white-paper/developer-guide-to-the-2023-owasp-top-10-for-api-security-wp-en.pdf)  
24. Hybrid App Security: Common Vulnerabilities and How to Fix Them ..., 2월 28, 2026에 액세스, [https://mohasoftware.com/blog/hybrid-app-security-common-vulnerabilities-and-how-to-fix-them](https://mohasoftware.com/blog/hybrid-app-security-common-vulnerabilities-and-how-to-fix-them)  
25. Security | Capacitor Documentation, 2월 28, 2026에 액세스, [https://capacitorjs.com/docs/guides/security](https://capacitorjs.com/docs/guides/security)  
26. Security Best Practices for Mobile Applications \- Bobcares, 2월 28, 2026에 액세스, [https://bobcares.com/blog/security-best-practices-for-mobile-applications/](https://bobcares.com/blog/security-best-practices-for-mobile-applications/)  
27. Security checklist \- Android Developers, 2월 28, 2026에 액세스, [https://developer.android.com/privacy-and-security/security-tips](https://developer.android.com/privacy-and-security/security-tips)  
28. iOS Code Signing: Certificates, Provisioning Profiles & Secure CI/CD | Appcircle, 2월 28, 2026에 액세스, [https://appcircle.io/guides/ios/ios-code-signing](https://appcircle.io/guides/ios/ios-code-signing)  
29. Claude Code overview \- Claude Code Docs, 2월 28, 2026에 액세스, [https://code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview)  
30. Complete Guide to CLAUDE.md and AGENTS.md 2026 | Data ..., 2월 28, 2026에 액세스, [https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9](https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9)  
31. Claude Code Tutorial for Beginners, 2월 28, 2026에 액세스, [https://www.youtube.com/watch?v=eMZmDH3T2bY\&vl=en](https://www.youtube.com/watch?v=eMZmDH3T2bY&vl=en)  
32. Security \- Claude Code Docs, 2월 28, 2026에 액세스, [https://code.claude.com/docs/en/security](https://code.claude.com/docs/en/security)  
33. Hardening Claude Code: A Security Review Framework and the Prompt That Does It For You | by Tim McAllister \- Medium, 2월 28, 2026에 액세스, [https://medium.com/@emergentcap/hardening-claude-code-a-security-review-framework-and-the-prompt-that-does-it-for-you-c546831f2cec](https://medium.com/@emergentcap/hardening-claude-code-a-security-review-framework-and-the-prompt-that-does-it-for-you-c546831f2cec)  
34. My actual real claude code setup that 2x my results (not an AI slop bullshit post to farm upvotes) \- Reposted : r/ClaudeCode \- Reddit, 2월 28, 2026에 액세스, [https://www.reddit.com/r/ClaudeCode/comments/1rbtbvz/my\_actual\_real\_claude\_code\_setup\_that\_2x\_my/](https://www.reddit.com/r/ClaudeCode/comments/1rbtbvz/my_actual_real_claude_code_setup_that_2x_my/)  
35. security-review | Skills Marketplace \- LobeHub, 2월 28, 2026에 액세스, [https://lobehub.com/skills/yeachan-heo-oh-my-claudecode-security-review](https://lobehub.com/skills/yeachan-heo-oh-my-claudecode-security-review)  
36. Security Audit: Comprehensive Claude Code Skill for OWASP \- MCP Market, 2월 28, 2026에 액세스, [https://mcpmarket.com/tools/skills/security-audit-4](https://mcpmarket.com/tools/skills/security-audit-4)