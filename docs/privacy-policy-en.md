# Privacy Policy

**Effective Date: March 1, 2026**

[Operator Name] (hereinafter "the Company") operates the PilaMatch service (hereinafter "the Service"), a Pilates/Yoga instructor-studio matching platform. The Company values the personal information of its users and complies with the Personal Information Protection Act (PIPA) of the Republic of Korea, the Act on Promotion of Information and Communications Network Utilization and Information Protection, and other relevant laws and regulations. This Privacy Policy describes how user information is collected, used, stored, and protected.

---

## 1. Purpose of Collection and Use of Personal Information

The Company collects and uses personal information for the following purposes. Collected personal information shall not be used beyond the stated purposes. If the purpose of use changes, prior consent will be obtained.

| Purpose Category | Specific Purpose |
|-----------------|-----------------|
| **Member Management** | Verification of membership registration intent, identity verification and authentication, member identification, prevention of unauthorized use, various notifications |
| **Service Provision** | Pilates/Yoga instructor-studio matching service, matching algorithm application, Trust Score calculation, contract management |
| **Payment and Settlement** | Escrow payment processing, deposit management, premium subscription payment, settlement processing, refund processing |
| **Identity Verification** | Mobile phone SMS verification, business registration number verification |
| **Customer Support** | User inquiry response, dispute mediation and resolution, no-show dispute processing |
| **Service Improvement** | Service usage statistical analysis, new service development and personalized service provision, service stability assurance |
| **Legal Compliance** | Record retention pursuant to the Act on Consumer Protection in Electronic Commerce and other relevant laws |

---

## 2. Personal Information Items Collected

### 2.1 Required Items

| Category | Items Collected | Collection Timing |
|----------|----------------|-------------------|
| **Membership Registration** | Email address, password (bcrypt hashed), name, member type (instructor/studio) | At registration |
| **Identity Verification** | Mobile phone number | At SMS verification |

### 2.2 Optional Items

| Category | Items Collected | Collection Timing |
|----------|----------------|-------------------|
| **Instructor Profile** | Profile photo, work experience, certification information, specialization areas, preferred regions, desired hourly rate, self-introduction | At profile creation |
| **Studio Profile** | Studio photos, facility information, location (address), operating hours, studio introduction | At profile creation |
| **Reviews** | Rating, review content | At review submission |

### 2.3 Business-related Items (Studio Members)

| Category | Items Collected | Collection Timing |
|----------|----------------|-------------------|
| **Business Verification** | Business registration number, business name, representative name | At business verification |

### 2.4 Payment-related Items

| Category | Items Collected | Collection Timing |
|----------|----------------|-------------------|
| **Payment Information** | Payment method details (card issuer, partial card number), payment amount, payment date/time, order number | At payment |
| **Settlement Information** | Settlement amount, settlement status | At contract completion |
| **Premium Subscription** | Billing key (tokenized), subscription status, payment history | At subscription payment |

> **Note**: Payment processing is handled through TossPayments. Sensitive payment information such as full card numbers is not stored on Company servers and is securely managed by TossPayments.

### 2.5 Automatically Collected Items

The following information may be automatically collected during service use.

| Items Collected | Collection Method |
|----------------|-------------------|
| IP address | Server logs |
| Device information (OS, browser type and version) | HTTP User-Agent |
| Access date/time and usage records | Server logs |
| Service usage records (matching history, contract history, application history) | Service database |
| JWT (JSON Web Token) authentication tokens | Issued upon authentication |

---

## 3. Retention and Use Period of Personal Information

### 3.1 General Principle

Personal information of users is destroyed without delay after the purpose of collection and use has been achieved. However, personal information is retained for 30 days after membership withdrawal to prevent re-registration abuse and for dispute resolution, after which it is destroyed.

### 3.2 Retention Required by Law

When retention is required by relevant laws and regulations, the Company retains personal information for the period prescribed by such laws as follows.

| Retained Items | Legal Basis | Retention Period |
|---------------|-------------|-----------------|
| Records related to contracts or subscription withdrawal | Act on Consumer Protection in Electronic Commerce | **5 years** |
| Records related to payment and supply of goods/services | Act on Consumer Protection in Electronic Commerce | **5 years** |
| Records related to consumer complaints or dispute resolution | Act on Consumer Protection in Electronic Commerce | **3 years** |
| Records related to labeling/advertising | Act on Consumer Protection in Electronic Commerce | **6 months** |
| Service visit records (login records, access logs) | Protection of Communications Secrets Act | **3 months** |

### 3.3 No-show Penalty Records

Records related to no-show penalties (report details, penalty imposition records, objection records) are retained for dispute resolution and service operation purposes until **1 year after account suspension is lifted** or **3 years after membership withdrawal**, whichever is later.

---

## 4. Provision of Personal Information to Third Parties

The Company does not, in principle, provide user personal information to external parties. However, exceptions are made in the following cases.

### 4.1 Provision with User Consent

| Recipient | Purpose | Items Provided | Retention Period |
|-----------|---------|---------------|-----------------|
| **Matching Counterpart** (Instructor or Studio) | Matching service provision, contract execution and performance | Name, profile information (experience, certifications, specialization, etc.) | 1 year after contract termination |

### 4.2 Outsourcing for Service Provision

| Outsourced Company | Outsourced Task | Items Provided | Notes |
|-------------------|-----------------|---------------|-------|
| **TossPayments (Viva Republica, Inc.)** | Payment processing, escrow payments, billing (recurring payments), refund processing | Payment amount, order number, payment method information | 5 years after payment completion (Act on Consumer Protection in Electronic Commerce) |
| **CoolSMS (CoolSMS Co., Ltd.)** | Mobile phone SMS verification, identity confirmation | Mobile phone number | Destroyed immediately upon verification completion |
| **National Tax Service (NTS) API** | Business registration number authenticity verification | Business registration number, representative name, business name | Destroyed immediately after verification (only verification result stored) |

### 4.3 Provision Required by Law

The Company may provide user personal information when required by law or when requested by investigative agencies through procedures and methods prescribed by law for investigation purposes.

---

## 5. Procedures and Methods for Destruction of Personal Information

### 5.1 Destruction Procedure

Information entered by users for purposes such as membership registration is transferred to a separate database (or separate filing cabinet for paper documents) after the purpose has been achieved and is destroyed after a certain period of storage in accordance with internal policies and information protection reasons under relevant laws.

- Upon membership withdrawal request: Destroyed **30 days** after withdrawal
- Items subject to legally mandated retention: Destroyed after the applicable retention period
- Dormant accounts: Separately stored and notified **1 year** after the last access date

### 5.2 Destruction Methods

| Storage Format | Destruction Method |
|---------------|-------------------|
| Electronic files | Deleted using technical methods that prevent reproduction (physical deletion of database records) |
| Paper documents | Shredded or incinerated |

### 5.3 Password Processing

User passwords are encrypted and stored using the bcrypt one-way hash algorithm, making original text restoration impossible. No one, including Company employees, can view the original text of user passwords.

---

## 6. Rights of Users and How to Exercise Them

### 6.1 User Rights

Users may exercise the following rights related to personal information protection at any time.

1. **Right to Access**: Users may request access to their personal information held by the Company.
2. **Right to Rectification**: Users may request correction of errors in their personal information.
3. **Right to Erasure**: Users may request deletion of their personal information. However, information that is required to be retained by law cannot be deleted.
4. **Right to Restriction of Processing**: Users may request the suspension of processing of their personal information.
5. **Right to Withdraw Consent**: Users may withdraw their consent to the collection and use of personal information.

### 6.2 How to Exercise Rights

| Method | Details |
|--------|---------|
| **In-service Settings** | Users can directly access, modify, and withdraw through [Profile Settings] > [Personal Information Management] menu within the service |
| **Email Request** | Request via the Privacy Officer's email (see below) |
| **Customer Support** | Inquiry through [Customer Support] menu within the service |

### 6.3 Processing Timeline

Requests for exercise of user rights are processed within **10 days** from the date of receipt, and the processing results are notified to the user. If there are legitimate reasons, the Company may notify the user of the reasons and postpone processing.

### 6.4 Exercise Through a Representative

Users may exercise their rights through a legal representative or an authorized delegate. In such cases, a power of attorney in the form prescribed by the Enforcement Rules of the Personal Information Protection Act (Form No. 11) must be submitted.

---

## 7. Measures to Ensure Security of Personal Information

The Company takes the following measures to ensure the security of personal information.

### 7.1 Technical Measures

| Measure | Details |
|---------|---------|
| **Password Encryption** | bcrypt one-way hash algorithm applied |
| **Authentication Token Security** | JWT (JSON Web Token) based authentication, Access Token expiration time setting, separate Refresh Token management |
| **Communication Encryption** | HTTPS (TLS 1.2 or higher) applied for data transmission encryption |
| **Access Control** | Role-Based Access Control (RBAC), authentication/authorization processing per API endpoint |
| **SQL Injection Prevention** | Parameter binding through SQLAlchemy ORM |
| **Input Validation** | Pydantic schema-based request data validation |

### 7.2 Administrative Measures

| Measure | Details |
|---------|---------|
| **Minimization of Personnel** | Limited number of personnel with access to personal information |
| **Regular Audits** | Regular self-audits on personal information protection |
| **Confidentiality Obligations** | Confidentiality training and obligation imposed on personnel handling personal information |

---

## 8. Privacy Officer

The Company designates a Privacy Officer as follows to take overall responsibility for personal information processing and to handle user complaints and damage relief related to personal information processing.

| Item | Details |
|------|---------|
| **Title** | Chief Privacy Officer (CPO) |
| **Organization** | [Operator Name] |
| **Email** | privacy@pilamatch.com |
| **Contact** | Via [Customer Support] menu within the service |

Users may direct all inquiries, complaints, and damage relief requests related to personal information protection that arise during the use of the service to the Privacy Officer. The Company will respond to and process user inquiries without delay.

---

## 9. Remedial Organizations for Personal Information Infringement

If you need to report or consult about personal information infringement, please contact the following organizations.

| Organization | Contact | Website |
|-------------|---------|---------|
| Personal Information Infringement Report Center (Korea Internet & Security Agency) | 118 (no area code) | [privacy.kisa.or.kr](https://privacy.kisa.or.kr) |
| Personal Information Dispute Mediation Committee | 1833-6972 (no area code) | [www.kopico.go.kr](https://www.kopico.go.kr) |
| Supreme Prosecutors' Office Cyber Investigation Division | 1301 (no area code) | [www.spo.go.kr](https://www.spo.go.kr) |
| National Police Agency Cyber Investigation Bureau | 182 (no area code) | [ecrm.police.go.kr](https://ecrm.police.go.kr) |

---

## 10. Use of Cookies

### 10.1 Purpose of Cookie Use

The Company uses cookies to provide individualized and customized services to users. Cookies are small text files that the service sends to the user's browser and are stored on the user's computer.

- JWT authentication token management
- Service usage settings maintenance
- Session management for security purposes

### 10.2 How to Refuse Cookie Settings

Users may refuse cookie storage through their web browser settings. However, refusing cookie storage may limit the use of services that require login.

- **Chrome**: Settings > Privacy and Security > Cookies and Other Site Data
- **Firefox**: Settings > Privacy & Security > Cookies and Site Data
- **Safari**: Preferences > Privacy

---

## 11. Changes to the Privacy Policy

This Privacy Policy may be amended due to changes in laws, policies, or services with additions, deletions, and modifications. When the Privacy Policy is changed, the Company will notify users through service announcements or email starting **7 days before** the effective date of the changes. However, for significant changes affecting user rights, notification will be given **30 days** in advance.

---

## 12. Supplementary Provisions

- **Effective Date**: March 1, 2026
- **Last Updated**: March 1, 2026
- This policy also applies to members who registered before the effective date of this policy.

---

*PilaMatch | [Operator Name]*
*Contact: privacy@pilamatch.com*
