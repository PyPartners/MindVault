## الوحدات الرئيسية

### 1. وحدة التشغيل الرئيسية (main.py)
- نقطة بداية البرنامج
- تستورد الوحدات الأخرى وتنسق بينها
- تتعامل مع إعداد البرنامج لأول مرة أو تسجيل الدخول

### 2. وحدة الواجهة (ui)
- **main_window.py**: الواجهة الرئيسية للبرنامج بعد تسجيل الدخول
- **dialogs.py**: نوافذ الحوار المختلفة (الإعداد، تسجيل الدخول، إضافة/تعديل حساب)
- **styles.py**: تطبيق السمات والأنماط على واجهة المستخدم

### 3. وحدة النواة (core)
- **crypto.py**: التشفير وفك التشفير للبيانات الحساسة
- **settings.py**: إدارة إعدادات البرنامج
- **translation.py**: دعم تعدد اللغات
- **utils.py**: أدوات مساعدة متنوعة

### 4. وحدة الميزات (features)
- **auto_lock.py**: القفل التلقائي للخزنة بعد فترة من عدم النشاط
- **backup_restore.py**: النسخ الاحتياطي واستعادة الخزنة
- **duplicate_checker.py**: التحقق من كلمات المرور المكررة
- **password_generator.py**: توليد كلمات مرور قوية
- **strength_indicator.py**: مؤشر قوة كلمة المرور
- **two_factor_auth.py**: المصادقة الثنائية

## تدفق التفاعل بين المستخدم والبرنامج

### مرحلة البداية
1. يبدأ البرنامج من main.py
2. يتحقق البرنامج من وجود ملف الخزنة:
   - إذا لم يكن موجوداً: يعرض نافذة الإعداد (SetupWindow)
   - إذا كان موجوداً: يعرض نافذة تسجيل الدخول (LoginWindow)

### مرحلة الإعداد (لأول مرة)
1. يدخل المستخدم كلمة مرور رئيسية
2. تستخدم وحدة strength_indicator لتقييم قوة كلمة المرور
3. عند التأكيد، تستخدم وحدة crypto لإنشاء خزنة جديدة مشفرة

### مرحلة تسجيل الدخول
1. يدخل المستخدم كلمة المرور الرئيسية
2. إذا كانت المصادقة الثنائية مفعلة (two_factor_auth)، يطلب رمز التحقق
3. تستخدم وحدة crypto لفك تشفير الخزنة
4. عند النجاح، يتم فتح النافذة الرئيسية (MainWindow)

### مرحلة استخدام البرنامج
1. تعرض النافذة الرئيسية قائمة الحسابات المخزنة
2. يمكن للمستخدم:
   - إضافة حساب جديد (AccountDialog)
   - تعديل حساب موجود (AccountDialog)
   - حذف حساب
   - نسخ كلمة مرور
   - البحث في الحسابات
   - الوصول للإعدادات (SettingsDialog)
   - استخدام الميزات المختلفة (النسخ الاحتياطي، التحقق من التكرار، إلخ)
3. تعمل وحدة auto_lock على قفل الخزنة تلقائياً بعد فترة من عدم النشاط

### مرحلة حفظ البيانات
1. عند إجراء أي تغيير (إضافة/تعديل/حذف)، يتم تحديث الخزنة في الذاكرة
2. تستخدم وحدة crypto لتشفير البيانات
3. يتم حفظ البيانات المشفرة في ملف الخزنة

### مرحلة الإغلاق
1. يمكن للمستخدم قفل الخزنة يدوياً
2. عند الخروج من البرنامج، يتم قفل الخزنة تلقائياً

## العلاقات الرئيسية بين الوحدات

- **main.py** ↔ **ui/dialogs.py**: لعرض نوافذ الإعداد وتسجيل الدخول
- **main.py** ↔ **ui/main_window.py**: لعرض النافذة الرئيسية بعد تسجيل الدخول
- **ui/main_window.py** ↔ **core/crypto.py**: لتشفير وفك تشفير البيانات
- **ui/main_window.py** ↔ **features/auto_lock.py**: لإدارة القفل التلقائي
- **ui/main_window.py** ↔ **features/backup_restore.py**: لإدارة النسخ الاحتياطي والاستعادة
- **ui/dialogs.py** ↔ **features/strength_indicator.py**: لعرض قوة كلمة المرور
- **ui/dialogs.py** ↔ **features/password_generator.py**: لتوليد كلمات مرور قوية
- **ui/dialogs.py** ↔ **features/duplicate_checker.py**: للتحقق من تكرار كلمات المرور
- **ui/dialogs.py** ↔ **features/two_factor_auth.py**: لإدارة المصادقة الثنائية
- **core/settings.py** ↔ **ui/main_window.py**: لتطبيق الإعدادات على الواجهة
- **core/translation.py** ↔ **ui**: لدعم تعدد اللغات في جميع واجهات المستخدم

-------------------------------------------------------------------------------------------

# Main Modules

## 1. Main Execution Module (main.py)
- The program entry point
- Imports and coordinates other modules
- Handles initial setup or user login

## 2. UI Module (ui)
- **main_window.py**: The main application window after login
- **dialogs.py**: Various dialog windows (setup, login, add/edit account)
- **styles.py**: Applies themes and styles to the UI

## 3. Core Module (core)
- **crypto.py**: Encryption and decryption of sensitive data
- **settings.py**: Manages program settings
- **translation.py**: Supports multiple languages
- **utils.py**: Various utility helper functions

## 4. Features Module (features)
- **auto_lock.py**: Auto-locks the vault after inactivity period
- **backup_restore.py**: Backup and restore vault data
- **duplicate_checker.py**: Checks for duplicate passwords
- **password_generator.py**: Generates strong passwords
- **strength_indicator.py**: Password strength indicator
- **two_factor_auth.py**: Two-factor authentication management

# User Interaction Flow

## Startup Phase
1. Program starts from main.py  
2. Checks if vault file exists:  
   - If not found: shows SetupWindow  
   - If found: shows LoginWindow

## Setup Phase (First Time Use)
1. User inputs master password  
2. Strength indicator module evaluates password strength  
3. On confirmation, crypto module creates a new encrypted vault

## Login Phase
1. User enters master password  
2. If two-factor authentication enabled, prompts for verification code  
3. Crypto module decrypts vault data  
4. On success, main window (MainWindow) opens

## Program Usage Phase
1. Main window displays the list of stored accounts  
2. User can:  
   - Add a new account (AccountDialog)  
   - Edit an existing account (AccountDialog)  
   - Delete an account  
   - Copy password  
   - Search accounts  
   - Access settings (SettingsDialog)  
   - Use various features (backup, duplicate checking, etc.)  
3. Auto-lock module locks the vault after inactivity automatically

## Data Saving Phase
1. On any change (add/edit/delete), vault data updates in memory  
2. Crypto module encrypts the data  
3. Encrypted data saves back to the vault file

## Closing Phase
1. User can manually lock the vault  
2. Vault auto-locks when the program closes

# Key Relationships Between Modules

- **main.py** ↔ **ui/dialogs.py**: To show setup and login dialogs  
- **main.py** ↔ **ui/main_window.py**: To display the main window after login  
- **ui/main_window.py** ↔ **core/crypto.py**: For encrypting and decrypting data  
- **ui/main_window.py** ↔ **features/auto_lock.py**: To manage auto-locking  
- **ui/main_window.py** ↔ **features/backup_restore.py**: To handle backup and restore  
- **ui/dialogs.py** ↔ **features/strength_indicator.py**: To show password strength  
- **ui/dialogs.py** ↔ **features/password_generator.py**: To generate strong passwords  
- **ui/dialogs.py** ↔ **features/duplicate_checker.py**: To check for duplicate passwords  
- **ui/dialogs.py** ↔ **features/two_factor_auth.py**: To manage two-factor authentication  
- **core/settings.py** ↔ **ui/main_window.py**: To apply settings on the UI  
- **core/translation.py** ↔ **ui**: To support multiple languages across all UI components
