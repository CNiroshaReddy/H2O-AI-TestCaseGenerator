import docx
import PyPDF2
import requests
from bs4 import BeautifulSoup
import re

class AIProcessor:
    def __init__(self):
        self.test_scenarios = []
    
    def process_documents(self, files_data, urls):
        """Process uploaded documents and URLs to generate test cases"""
        # Write to debug file
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write("\n" + "="*60 + "\n")
            f.write("AI PROCESSOR - PROCESS_DOCUMENTS CALLED!\n")
            f.write("="*60 + "\n")
            f.write(f"Files to process: {len(files_data)}\n")
            f.write(f"URLs to process: {len(urls)}\n")
        
        print("\n" + "="*60)
        print("AI PROCESSOR - PROCESS_DOCUMENTS CALLED!")
        print("="*60)
        print(f"Files to process: {len(files_data)}")
        print(f"URLs to process: {len(urls)}")
        
        all_content = []
        
        # Process uploaded files
        for file_data in files_data:
            msg = f"\nExtracting content from file: {file_data['name']}"
            print(msg)
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(msg + "\n")
            
            content = self._extract_content(file_data['path'], file_data['type'])
            
            msg = f"Extracted {len(content)} characters from {file_data['name']}"
            print(msg)
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(msg + "\n")
                f.write(f"Content preview: {content[:200]}\n")
            
            all_content.append(content)
        
        # Process URLs
        for url in urls:
            msg = f"\nExtracting content from URL: {url}"
            print(msg)
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(msg + "\n")
            
            content = self._extract_url_content(url)
            
            msg = f"Extracted {len(content)} characters from URL"
            print(msg)
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(msg + "\n")
            
            all_content.append(content)
        
        # Generate test scenarios and cases
        combined_content = "\n\n".join(all_content)
        
        msg = f"\nTotal combined content: {len(combined_content)} characters"
        print(msg)
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(msg + "\n")
            f.write(f"Combined content preview:\n{combined_content[:500]}\n")
        
        print("\nStarting test case generation...")
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write("Starting test case generation...\n")
        
        return self._generate_test_cases(combined_content)
    
    def _extract_content(self, file_path, file_type):
        """Extract text from uploaded documents"""
        if file_type in ['docx']:
            return self._extract_docx(file_path)
        elif file_type == 'doc':
            # Old .doc format - try to read as text or suggest conversion
            print(f"WARNING: Old .doc format detected. Attempting text extraction...")
            try:
                # Try reading as plain text (works for some .doc files)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Clean up binary artifacts
                    content = ''.join(char for char in content if char.isprintable() or char in '\n\r\t')
                    if len(content.strip()) > 50:
                        return content
            except:
                pass
            
            print("Could not extract from .doc file. Please save as .docx or .txt format.")
            return ""
        elif file_type == 'pdf':
            return self._extract_pdf(file_path)
        elif file_type == 'txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return ""
        return ""
    
    def _extract_docx(self, file_path):
        """Extract text from Word document"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            
            # If no text extracted, it might be an old .doc file
            if not text or len(text.strip()) == 0:
                print(f"WARNING: No text extracted from {file_path}")
                print("This might be an old .doc file (not .docx). Please save as .docx or .txt format.")
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"WARNING: No text extracted from {file_path}\n")
                    f.write("File might be old .doc format. python-docx only supports .docx\n")
            
            return text
        except Exception as e:
            print(f"Error extracting DOCX: {str(e)}")
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"Error extracting DOCX: {str(e)}\n")
            return ""
    
    def _extract_pdf(self, file_path):
        """Extract text from PDF"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except:
            return ""
    
    def _extract_url_content(self, url):
        """Extract content from webpage with structured analysis"""
        try:
            # Use selenium-like headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            session = requests.Session()
            response = session.get(url, timeout=15, headers=headers, allow_redirects=True)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            print(f"\n=== Extracting content from {url} ===")
            print(f"Response status: {response.status_code}")
            
            # Extract structured information
            content_parts = []
            content_parts.append(f"\n=== WEBPAGE ANALYSIS: {url} ===")
            
            # Extract title
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
                content_parts.append(f"Website: {title}")
            
            # Remove script, style, and other non-content elements
            for element in soup(["script", "style", "meta", "noscript", "iframe"]):
                element.decompose()
            
            # Extract main text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            text_content = ' '.join(text_content.split())
            
            # Extract meaningful sentences (longer than 20 chars)
            sentences = [s.strip() + '.' for s in text_content.split('.') if len(s.strip()) > 20]
            
            if sentences:
                content_parts.append("\nContent Analysis:")
                content_parts.extend(sentences[:50])  # First 50 sentences
            
            # Extract links text
            links = [a.get_text(strip=True) for a in soup.find_all('a', href=True) if a.get_text(strip=True) and len(a.get_text(strip=True)) > 2]
            if links:
                content_parts.append(f"\nNavigation/Links: {', '.join(set(links[:30]))}")
            
            # Extract button text
            buttons = []
            for btn in soup.find_all(['button', 'input']):
                btn_text = btn.get_text(strip=True) or btn.get('value', '') or btn.get('aria-label', '') or btn.get('placeholder', '')
                if btn_text and len(btn_text) > 1:
                    buttons.append(btn_text)
            if buttons:
                content_parts.append(f"\nActions/Buttons: {', '.join(set(buttons[:20]))}")
            
            result = "\n".join(content_parts)
            print(f"Extracted {len(result)} characters from webpage")
            
            # If very little content extracted, infer from URL domain
            if len(result) < 500:
                print("WARNING: Limited content extracted, inferring from URL")
                domain_lower = url.lower()
                
                # Infer website type and add relevant features
                inferred_features = []
                
                if 'amazon' in domain_lower or 'shop' in domain_lower or 'store' in domain_lower:
                    inferred_features.append("\n\nINFERRED E-COMMERCE FEATURES:")
                    inferred_features.append("- User Registration and Login")
                    inferred_features.append("- Product Search and Filtering")
                    inferred_features.append("- Product Details and Images")
                    inferred_features.append("- Shopping Cart Management")
                    inferred_features.append("- Checkout Process")
                    inferred_features.append("- Payment Processing")
                    inferred_features.append("- Order Tracking")
                    inferred_features.append("- Product Reviews and Ratings")
                    inferred_features.append("- Wishlist Functionality")
                    inferred_features.append("- Customer Account Management")
                    inferred_features.append("- Shipping and Delivery Options")
                    inferred_features.append("- Return and Refund Process")
                
                elif 'bank' in domain_lower or 'finance' in domain_lower:
                    inferred_features.append("\n\nINFERRED BANKING FEATURES:")
                    inferred_features.append("- Secure Login with 2FA")
                    inferred_features.append("- Account Balance View")
                    inferred_features.append("- Fund Transfer")
                    inferred_features.append("- Transaction History")
                    inferred_features.append("- Bill Payment")
                
                elif 'social' in domain_lower or 'facebook' in domain_lower or 'twitter' in domain_lower:
                    inferred_features.append("\n\nINFERRED SOCIAL MEDIA FEATURES:")
                    inferred_features.append("- User Registration and Profile")
                    inferred_features.append("- Post Creation and Sharing")
                    inferred_features.append("- Like, Comment, Share")
                    inferred_features.append("- Friend/Follow System")
                    inferred_features.append("- Messaging")
                
                else:
                    inferred_features.append("\n\nINFERRED WEB APPLICATION FEATURES:")
                    inferred_features.append("- User Authentication (Login/Register)")
                    inferred_features.append("- User Profile Management")
                    inferred_features.append("- Search Functionality")
                    inferred_features.append("- Data Entry Forms")
                    inferred_features.append("- Data Display and Retrieval")
                    inferred_features.append("- Navigation Menu")
                
                result += "\n".join(inferred_features)
            
            return result
        except Exception as e:
            print(f"Error extracting URL: {str(e)}")
            return ""
    
    def _generate_test_cases(self, content):
        """AI logic to generate test scenarios and test cases from any content"""
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n=== Analyzing content ({len(content)} characters) ===\n")
        
        print(f"\n=== Analyzing content ({len(content)} characters) ===")
        
        results = []
        features = self._intelligent_feature_extraction(content)
        
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"Features extracted: {len(features)}\n")
        
        ts_counter = 1
        tc_counter = 1  # Global TC counter across all scenarios
        
        for feature in features:
            scenario = {
                'ts_id': f'TS_{ts_counter:02d}',
                'scenario_desc': feature['description'],
                'test_cases': []
            }
            
            for test_case in feature['test_cases']:
                tc = {
                    'tc_id': f'TC_{tc_counter:02d}',
                    'steps': test_case['steps'],
                    'expected': test_case['expected'],
                    'test_data': test_case.get('test_data', ''),
                    'results': '',
                    'defects': '',
                    'comments': ''
                }
                scenario['test_cases'].append(tc)
                tc_counter += 1  # Increment globally
            
            results.append(scenario)
            ts_counter += 1
        
        msg = f"Generated {len(results)} test scenarios with {tc_counter-1} test cases"
        print(msg)
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(msg + "\n")
        
        return results
    
    def _intelligent_feature_extraction(self, content):
        """Intelligently extract features and workflows from any content"""
        features = []
        content_lower = content.lower()
        
        print(f"\n=== Content Preview ===")
        print(content[:500] if len(content) > 500 else content)
        
        # Identify action verbs and functional keywords
        action_patterns = {
            'authentication': ['login', 'log in', 'sign in', 'signin', 'authenticate', 'register', 'sign up', 'signup', 'logout', 'log out', 'credentials', 'email', 'password', 'remember me'],
            'data_entry': ['enter', 'input', 'fill', 'type', 'submit', 'create', 'add', 'insert', 'form'],
            'data_modification': ['edit', 'update', 'modify', 'change', 'delete', 'remove'],
            'data_retrieval': ['view', 'display', 'show', 'list', 'retrieve', 'get', 'fetch', 'read', 'dashboard'],
            'search': ['search', 'find', 'filter', 'query', 'lookup'],
            'navigation': ['navigate', 'go to', 'click', 'select', 'open', 'access', 'redirect'],
            'file_operations': ['upload', 'download', 'attach', 'import', 'export', 'save'],
            'transaction': ['purchase', 'buy', 'checkout', 'pay', 'payment', 'order', 'cart'],
            'communication': ['send', 'email', 'notify', 'message', 'alert', 'notification'],
            'validation': ['validate', 'verify', 'check', 'confirm', 'ensure', 'error', 'incorrect', 'failed', 'invalid'],
            'reporting': ['report', 'generate', 'export', 'print', 'download report'],
            'configuration': ['configure', 'settings', 'setup', 'preferences', 'options'],
            'security': ['security', 'secure', 'lockout', 'lock', 'session', 'timeout', 'sql injection', 'xss', 'https', 'encrypt'],
            'responsive': ['responsive', 'mobile', 'desktop', 'tablet', 'screen size', 'layout', 'web', 'device']
        }
        
        # Detect which functionalities are present
        detected_features = {}
        for category, keywords in action_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    if category not in detected_features:
                        detected_features[category] = []
                    # Extract context around the keyword
                    context = self._extract_context(content, keyword)
                    if context:
                        detected_features[category].append(context)
        
        print(f"Detected features: {list(detected_features.keys())}")
        print(f"Number of contexts per feature: {[(k, len(v)) for k, v in detected_features.items()]}")
        
        # Generate test scenarios for each detected feature
        for category, contexts in detected_features.items():
            print(f"\nGenerating tests for category: {category}")
            feature_tests = self._generate_feature_test_cases(category, contexts, content)
            if feature_tests:
                print(f"Generated {len(feature_tests)} test scenario groups for {category}")
                features.extend(feature_tests)
            else:
                print(f"No tests generated for {category}")
        
        # If no specific features detected, analyze content structure
        if not features:
            features = self._generate_generic_tests(content)
        
        return features[:25]  # Limit to 25 scenarios for comprehensive coverage
    
    def _extract_context(self, content, keyword, window=150):
        """Extract context around a keyword"""
        content_lower = content.lower()
        index = content_lower.find(keyword)
        if index != -1:
            start = max(0, index - window)
            end = min(len(content), index + len(keyword) + window)
            context = content[start:end].strip()
            # Clean up context
            context = ' '.join(context.split())
            return context
        return None
    
    def _generate_feature_test_cases(self, category, contexts, full_content):
        """Generate comprehensive test cases covering all testing types"""
        features = []
        context_sample = contexts[0][:100] if contexts else ""
        
        if category == 'authentication':
            # POSITIVE TEST CASES
            features.append({
                'description': 'Login with valid credentials - Positive Testing',
                'test_cases': [
                    {
                        'steps': '1. Navigate to login page\n2. Enter valid registered email address\n3. Enter correct password\n4. Click Login button\n5. Verify redirect to dashboard',
                        'expected': 'User successfully logs in and is redirected to personalized dashboard',
                        'test_data': 'Email: user@example.com, Password: Test@123'
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Enter valid email\n3. Enter correct password\n4. Check "Remember Me" checkbox\n5. Click Login\n6. Close browser\n7. Reopen browser and access application',
                        'expected': 'User remains logged in and session persists across browser sessions',
                        'test_data': 'Email: user@example.com, Password: Test@123, Remember Me: Checked'
                    }
                ]
            })
            
            # NEGATIVE TEST CASES
            features.append({
                'description': 'Login with invalid credentials - Negative Testing',
                'test_cases': [
                    {
                        'steps': '1. Navigate to login page\n2. Enter valid email\n3. Enter incorrect password\n4. Click Login button\n5. Verify error message displayed',
                        'expected': 'Login fails with error message "Invalid email or password"',
                        'test_data': 'Email: user@example.com, Password: WrongPass123'
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Enter unregistered email\n3. Enter any password\n4. Click Login button\n5. Verify error message',
                        'expected': 'Login fails with error message "Account not found"',
                        'test_data': 'Email: notregistered@example.com, Password: AnyPass123'
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Leave email field empty\n3. Enter password\n4. Click Login button\n5. Verify validation error',
                        'expected': 'Validation error displayed: "Email is required"',
                        'test_data': 'Email: (empty), Password: Test@123'
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Enter email\n3. Leave password field empty\n4. Click Login button\n5. Verify validation error',
                        'expected': 'Validation error displayed: "Password is required"',
                        'test_data': 'Email: user@example.com, Password: (empty)'
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Leave both email and password empty\n3. Click Login button\n4. Verify validation errors for both fields',
                        'expected': 'Validation errors displayed for both email and password fields',
                        'test_data': 'Email: (empty), Password: (empty)'
                    }
                ]
            })
            
            # BOUNDARY/EDGE CASES
            features.append({
                'description': 'Login with boundary and edge case inputs',
                'test_cases': [
                    {
                        'steps': '1. Navigate to login page\n2. Enter email with maximum allowed length (254 characters)\n3. Enter valid password\n4. Click Login\n5. Verify system handles correctly',
                        'expected': 'System accepts maximum length email and processes login correctly',
                        'test_data': 'Email: very_long_email_address_with_254_characters@example.com, Password: Test@123'
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Enter email with special characters\n3. Enter password\n4. Click Login\n5. Verify system handles special characters',
                        'expected': 'System correctly processes email with special characters',
                        'test_data': 'Email: user+test@example.com, Password: Test@123'
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Enter email with leading/trailing spaces\n3. Enter password\n4. Click Login\n5. Verify system trims spaces',
                        'expected': 'System trims spaces and processes login correctly',
                        'test_data': 'Email: " user@example.com ", Password: Test@123'
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Enter password with minimum length (8 characters)\n3. Verify acceptance\n4. Enter password with maximum length (128 characters)\n5. Verify acceptance',
                        'expected': 'System accepts passwords within defined length boundaries',
                        'test_data': 'Min: Test@123, Max: 128 character password'
                    }
                ]
            })
            
            # SECURITY TEST CASES
            features.append({
                'description': 'Login security and vulnerability testing',
                'test_cases': [
                    {
                        'steps': '1. Navigate to login page\n2. Enter SQL injection code in email field\n3. Enter password\n4. Click Login\n5. Verify system prevents SQL injection',
                        'expected': 'System sanitizes input and prevents SQL injection attack, login fails safely',
                        'test_data': "Email: admin' OR '1'='1, Password: test"
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Enter XSS script in email field\n3. Click Login\n4. Verify script is not executed\n5. Check output is escaped',
                        'expected': 'System prevents XSS attack by escaping special characters',
                        'test_data': 'Email: <script>alert("XSS")</script>@test.com'
                    },
                    {
                        'steps': '1. Enter wrong password 5 times consecutively\n2. Verify account lockout after 5 attempts\n3. Try to login with correct password\n4. Verify account is locked\n5. Check lockout duration',
                        'expected': 'Account is locked after 5 failed attempts, displays lockout message with duration',
                        'test_data': '5 consecutive failed login attempts'
                    },
                    {
                        'steps': '1. Login successfully\n2. Copy session token/cookie\n3. Logout\n4. Try to use old session token to access protected page\n5. Verify access denied',
                        'expected': 'Old session tokens are invalidated after logout, access is denied',
                        'test_data': 'Session token from previous session'
                    },
                    {
                        'steps': '1. Login successfully\n2. Remain idle for 30 minutes\n3. Try to perform any action\n4. Verify session timeout\n5. Check redirect to login page',
                        'expected': 'Session expires after 30 minutes of inactivity, user is redirected to login',
                        'test_data': 'Session timeout: 30 minutes'
                    },
                    {
                        'steps': '1. Open login page\n2. Check if page uses HTTPS protocol\n3. Verify SSL certificate is valid\n4. Check password field is masked\n5. Verify no sensitive data in URL',
                        'expected': 'Login page uses HTTPS, SSL certificate valid, password masked, no data in URL',
                        'test_data': 'Security protocol check'
                    }
                ]
            })
            
            # UI/UX TEST CASES
            features.append({
                'description': 'Login UI/UX and responsive design testing',
                'test_cases': [
                    {
                        'steps': '1. Open login page on desktop browser (1920x1080)\n2. Verify all elements are visible\n3. Check field alignment\n4. Verify button placement\n5. Test on different desktop resolutions',
                        'expected': 'Login page displays correctly on desktop with proper layout and alignment',
                        'test_data': 'Desktop resolutions: 1920x1080, 1366x768, 1280x720'
                    },
                    {
                        'steps': '1. Open login page on mobile device (iPhone)\n2. Verify responsive layout\n3. Check touch-friendly buttons\n4. Test portrait and landscape modes\n5. Verify keyboard doesn\'t hide fields',
                        'expected': 'Login page is fully responsive on mobile devices with touch-friendly interface',
                        'test_data': 'Mobile devices: iPhone 12, Samsung Galaxy S21'
                    },
                    {
                        'steps': '1. Open login page on tablet (iPad)\n2. Verify layout adapts to tablet size\n3. Test portrait and landscape\n4. Check touch interactions\n5. Verify all elements accessible',
                        'expected': 'Login page works correctly on tablets with appropriate layout',
                        'test_data': 'Tablets: iPad Pro, Samsung Galaxy Tab'
                    },
                    {
                        'steps': '1. Navigate to login page\n2. Verify password field shows masked characters (dots/asterisks)\n3. Click show/hide password icon\n4. Verify password becomes visible\n5. Click again to hide',
                        'expected': 'Password masking works correctly with toggle functionality',
                        'test_data': 'Password visibility toggle'
                    },
                    {
                        'steps': '1. Open login page\n2. Use Tab key to navigate between fields\n3. Verify focus moves correctly (email → password → remember me → login button)\n4. Press Enter on login button\n5. Verify form submits',
                        'expected': 'Keyboard navigation works correctly, Enter key submits form',
                        'test_data': 'Keyboard navigation test'
                    },
                    {
                        'steps': '1. Open login page\n2. Verify email field has auto-focus\n3. Check placeholder text is visible\n4. Verify field labels are clear\n5. Check error messages are readable',
                        'expected': 'UI elements are user-friendly with clear labels and helpful text',
                        'test_data': 'UI/UX elements check'
                    }
                ]
            })
            
            # PERFORMANCE TEST CASES
            features.append({
                'description': 'Login performance and load testing',
                'test_cases': [
                    {
                        'steps': '1. Navigate to login page\n2. Enter credentials\n3. Click Login\n4. Measure time from click to dashboard load\n5. Verify response time is under 2 seconds',
                        'expected': 'Login completes within 2 seconds under normal load',
                        'test_data': 'Performance benchmark: < 2 seconds'
                    },
                    {
                        'steps': '1. Simulate 100 concurrent users logging in\n2. Measure response times\n3. Check for errors\n4. Verify all logins complete successfully\n5. Monitor server resources',
                        'expected': 'System handles 100 concurrent logins without performance degradation',
                        'test_data': '100 concurrent users'
                    },
                    {
                        'steps': '1. Simulate 1000 concurrent users\n2. Measure response times\n3. Check error rates\n4. Monitor CPU and memory usage\n5. Verify system stability',
                        'expected': 'System remains stable under load of 1000 concurrent users',
                        'test_data': '1000 concurrent users'
                    },
                    {
                        'steps': '1. Measure login page load time\n2. Check time to first byte (TTFB)\n3. Measure DOM content loaded time\n4. Verify page fully loads in under 3 seconds\n5. Test on different network speeds',
                        'expected': 'Login page loads completely within 3 seconds on standard network',
                        'test_data': 'Network speeds: 4G, 3G, WiFi'
                    }
                ]
            })
            
            # INTEGRATION TEST CASES
            features.append({
                'description': 'Login integration with other systems',
                'test_cases': [
                    {
                        'steps': '1. Login successfully\n2. Verify session is created in database\n3. Check user data is retrieved correctly\n4. Verify dashboard loads with user-specific data\n5. Check all integrated services are accessible',
                        'expected': 'Login integrates correctly with database and all dependent services',
                        'test_data': 'Database and service integration'
                    },
                    {
                        'steps': '1. Simulate database connection failure\n2. Attempt to login\n3. Verify graceful error handling\n4. Check appropriate error message displayed\n5. Verify system doesn\'t crash',
                        'expected': 'System handles database failures gracefully with user-friendly error message',
                        'test_data': 'Database connection failure simulation'
                    },
                    {
                        'steps': '1. Login from one browser\n2. Login from another browser with same credentials\n3. Verify concurrent session handling\n4. Check if previous session is invalidated or both allowed\n5. Verify session management policy',
                        'expected': 'System handles concurrent sessions according to defined policy',
                        'test_data': 'Multiple concurrent sessions'
                    }
                ]
            })
            
            # ERROR HANDLING TEST CASES
            features.append({
                'description': 'Login error handling and recovery',
                'test_cases': [
                    {
                        'steps': '1. Disconnect network\n2. Attempt to login\n3. Verify network error is caught\n4. Check error message is displayed\n5. Reconnect and retry',
                        'expected': 'System displays clear network error message and allows retry after reconnection',
                        'test_data': 'Network disconnection scenario'
                    },
                    {
                        'steps': '1. Enter valid credentials\n2. Simulate server timeout during authentication\n3. Verify timeout is handled\n4. Check appropriate message displayed\n5. Verify user can retry',
                        'expected': 'System handles server timeout gracefully with retry option',
                        'test_data': 'Server timeout: 30 seconds'
                    },
                    {
                        'steps': '1. Enter credentials\n2. Simulate 500 Internal Server Error\n3. Verify error is caught\n4. Check user-friendly error message\n5. Verify system doesn\'t expose technical details',
                        'expected': 'System displays generic error message without exposing technical details',
                        'test_data': '500 Internal Server Error'
                    },
                    {
                        'steps': '1. Login with locked account\n2. Verify lockout message is displayed\n3. Check lockout duration is shown\n4. Verify contact support option available\n5. Test account unlock after duration',
                        'expected': 'Clear lockout message with duration and support contact information',
                        'test_data': 'Locked account scenario'
                    }
                ]
            })
        
        elif category == 'search':
            # Positive scenarios
            features.append({
                'description': 'Product/content search with valid inputs',
                'test_cases': [
                    {
                        'steps': '1. Open the application\n2. Locate search field/box\n3. Enter valid search keyword\n4. Click search button or press Enter\n5. Verify search results are displayed\n6. Verify results match search criteria',
                        'expected': 'Relevant results matching the search keyword are displayed in proper format',
                        'test_data': 'Search keyword: "laptop"'
                    },
                    {
                        'steps': '1. Navigate to search\n2. Enter partial keyword\n3. Verify auto-suggestions appear\n4. Select a suggestion\n5. Verify search executes with selected term',
                        'expected': 'Auto-complete suggestions appear and selecting one performs search',
                        'test_data': 'Partial keyword: "lap"'
                    },
                    {
                        'steps': '1. Perform a search\n2. Apply filters (price, category, rating)\n3. Verify filtered results\n4. Sort results by relevance/price\n5. Verify sorting works',
                        'expected': 'Search results can be filtered and sorted correctly',
                        'test_data': 'Filters: Price $100-$500, Category: Electronics'
                    }
                ]
            })
            
            # Negative scenarios
            features.append({
                'description': 'Search with invalid or edge case inputs',
                'test_cases': [
                    {
                        'steps': '1. Navigate to search page\n2. Enter search term with special characters (@, #, $, %)\n3. Click search button\n4. Verify system handles special characters\n5. Check for errors',
                        'expected': 'System processes special characters without errors or displays appropriate message',
                        'test_data': 'Special characters: @#$%test'
                    },
                    {
                        'steps': '1. Open search functionality\n2. Enter non-existent or invalid search term\n3. Click search button\n4. Verify "no results found" message\n5. Check for alternative suggestions',
                        'expected': 'System displays "No results found" message with helpful suggestions or alternatives',
                        'test_data': 'Invalid term: "xyzabc123notfound"'
                    },
                    {
                        'steps': '1. Navigate to search\n2. Leave search field empty\n3. Click search button\n4. Verify validation or behavior',
                        'expected': 'System either shows validation error or displays all items/default results',
                        'test_data': 'Empty search field'
                    },
                    {
                        'steps': '1. Enter extremely long search query (500+ characters)\n2. Click search\n3. Verify system handles gracefully',
                        'expected': 'System either truncates query or displays character limit message',
                        'test_data': 'Very long search string'
                    }
                ]
            })
            
            # Performance scenarios
            features.append({
                'description': 'Search performance and response time',
                'test_cases': [
                    {
                        'steps': '1. Enter search keyword\n2. Measure time from click to results display\n3. Verify response time is under 3 seconds\n4. Check for loading indicators',
                        'expected': 'Search results load within acceptable time (< 3 seconds) with loading indicator',
                        'test_data': 'Performance benchmark'
                    },
                    {
                        'steps': '1. Perform multiple rapid searches\n2. Verify each search completes\n3. Check for race conditions\n4. Verify latest search results are shown',
                        'expected': 'System handles rapid consecutive searches without errors',
                        'test_data': 'Multiple rapid searches'
                    }
                ]
            })
            
            # Security scenarios
            features.append({
                'description': 'Search security and injection prevention',
                'test_cases': [
                    {
                        'steps': '1. Enter SQL injection code in search\n2. Execute search\n3. Verify system sanitizes input\n4. Check no database errors occur',
                        'expected': 'System prevents SQL injection and handles input securely',
                        'test_data': "Search: ' OR '1'='1"
                    },
                    {
                        'steps': '1. Enter XSS script in search field\n2. Execute search\n3. Verify script is not executed\n4. Check output is properly escaped',
                        'expected': 'System prevents XSS attacks by escaping special characters',
                        'test_data': 'Search: <script>alert("XSS")</script>'
                    }
                ]
            })
        
        elif category == 'data_entry':
            features.append({
                'description': 'Data entry form submission and validation',
                'test_cases': [
                    {
                        'steps': '1. Navigate to data entry form page\n2. Identify all required fields\n3. Fill all required fields with valid data\n4. Fill optional fields if any\n5. Click submit button\n6. Verify success message',
                        'expected': 'Data is saved successfully, confirmation message is displayed, and form is cleared or redirected',
                        'test_data': 'Name: John Doe, Email: john@example.com, Phone: 1234567890'
                    },
                    {
                        'steps': '1. Open data entry form\n2. Leave all required fields empty\n3. Click submit button\n4. Verify validation error messages\n5. Check that form is not submitted',
                        'expected': 'System displays validation errors for all required fields and prevents form submission',
                        'test_data': 'All fields empty'
                    },
                    {
                        'steps': '1. Navigate to form\n2. Enter invalid data format (e.g., text in number field, invalid email)\n3. Click submit button\n4. Verify format validation errors',
                        'expected': 'System validates data format and displays specific error messages for each invalid field',
                        'test_data': 'Email: notanemail, Phone: abcd'
                    },
                    {
                        'steps': '1. Open form\n2. Enter boundary values (minimum and maximum allowed)\n3. Submit form\n4. Verify system accepts boundary values',
                        'expected': 'System correctly handles and accepts boundary value inputs without errors',
                        'test_data': 'Min/Max values as per field constraints'
                    },
                    {
                        'steps': '1. Fill form with valid data\n2. Click cancel or back button\n3. Verify data is not saved\n4. Check form state',
                        'expected': 'Form data is discarded and user is returned to previous page without saving',
                        'test_data': 'Any valid data'
                    }
                ]
            })
        
        elif category == 'data_modification':
            features.append({
                'description': 'Data update and delete operations',
                'test_cases': [
                    {
                        'steps': '1. Navigate to records list\n2. Select an existing record\n3. Click edit/modify button\n4. Update one or more field values\n5. Click save button\n6. Verify success message\n7. Check updated values are displayed',
                        'expected': 'Data is updated successfully, changes are saved to database, and updated values are reflected immediately',
                        'test_data': 'Updated values: Name: Jane Smith, Email: jane.smith@example.com'
                    },
                    {
                        'steps': '1. Open record for editing\n2. Make changes to fields\n3. Click cancel button (without saving)\n4. Verify confirmation dialog if any\n5. Check original data remains unchanged',
                        'expected': 'Changes are discarded, original data remains unchanged, and user returns to previous view',
                        'test_data': 'Modified data (not saved)'
                    },
                    {
                        'steps': '1. Navigate to records list\n2. Select record to delete\n3. Click delete button\n4. Verify confirmation dialog appears\n5. Confirm deletion\n6. Verify success message\n7. Check record is removed from list',
                        'expected': 'Record is deleted successfully from database and no longer appears in the system',
                        'test_data': 'Record ID: 12345'
                    },
                    {
                        'steps': '1. Select record to delete\n2. Click delete button\n3. When confirmation dialog appears, click cancel\n4. Verify record is not deleted\n5. Check record still exists',
                        'expected': 'Deletion is cancelled and record remains in the system unchanged',
                        'test_data': 'Record ID: 12345'
                    }
                ]
            })
        
        elif category == 'data_retrieval':
            features.append({
                'description': 'Data display and retrieval functionality',
                'test_cases': [
                    {
                        'steps': '1. Navigate to data view/list page\n2. Wait for page to load\n3. Verify all records are displayed\n4. Check data accuracy\n5. Verify column headers\n6. Check pagination if applicable',
                        'expected': 'All data records are displayed correctly with accurate information in proper format',
                        'test_data': 'Existing database records'
                    },
                    {
                        'steps': '1. Navigate to data list\n2. Apply filter criteria (e.g., date range, category, status)\n3. Click apply filter\n4. Verify filtered results\n5. Clear filters\n6. Verify all data returns',
                        'expected': 'Data is filtered correctly based on selected criteria and all data returns when filters are cleared',
                        'test_data': 'Filter: Date range 01/01/2024 to 31/01/2024'
                    },
                    {
                        'steps': '1. View data list\n2. Click on column header to sort\n3. Verify data is sorted (ascending)\n4. Click again to sort descending\n5. Verify sort order changes',
                        'expected': 'Data is sorted correctly in ascending and descending order based on selected column',
                        'test_data': 'Sort by: Name, Date, Price'
                    },
                    {
                        'steps': '1. Navigate to data list\n2. Click on specific record\n3. View detailed information page\n4. Verify all details are displayed\n5. Check data completeness',
                        'expected': 'Detailed view shows complete and accurate record information with all fields populated',
                        'test_data': 'Record ID: 12345'
                    }
                ]
            })
        
        elif category == 'file_operations':
            features.append({
                'description': 'File upload and download operations',
                'test_cases': [
                    {
                        'steps': '1. Navigate to file upload section\n2. Click "Choose File" or "Upload" button\n3. Select valid file from system (PDF, DOC, or Image)\n4. Click "Upload" to confirm\n5. Wait for upload to complete\n6. Verify success message and file appears in list',
                        'expected': 'File is uploaded successfully, confirmation message is displayed, and file appears in uploaded files list',
                        'test_data': 'Valid file: document.pdf (2MB)'
                    },
                    {
                        'steps': '1. Navigate to upload section\n2. Attempt to upload unsupported file type (e.g., .exe, .zip)\n3. Click upload\n4. Verify error message\n5. Check file is not uploaded',
                        'expected': 'System rejects unsupported file types and displays "File type not supported" error message',
                        'test_data': 'Unsupported file: program.exe'
                    },
                    {
                        'steps': '1. Navigate to upload section\n2. Select file exceeding maximum size limit\n3. Attempt to upload\n4. Verify size validation error\n5. Check upload fails',
                        'expected': 'System displays "File size exceeds limit" error and prevents upload',
                        'test_data': 'Large file: video.mp4 (50MB) with 10MB limit'
                    },
                    {
                        'steps': '1. Navigate to uploaded files list\n2. Locate previously uploaded file\n3. Click download button/link\n4. Wait for download to complete\n5. Open downloaded file\n6. Verify file integrity and content',
                        'expected': 'File downloads successfully to local system and content is intact without corruption',
                        'test_data': 'Previously uploaded file'
                    }
                ]
            })
        
        elif category == 'transaction':
            # Positive scenarios
            features.append({
                'description': 'Add products to shopping cart',
                'test_cases': [
                    {
                        'steps': '1. Browse products on website\n2. Select a product\n3. Click "Add to Cart" button\n4. Verify item is added to cart\n5. Check cart icon/count updates\n6. Navigate to cart page\n7. Verify product details in cart',
                        'expected': 'Product is successfully added to cart, cart count updates, and product appears in cart with correct details',
                        'test_data': 'Product: Laptop, Quantity: 1, Price: $999'
                    },
                    {
                        'steps': '1. Add same product multiple times\n2. Navigate to cart\n3. Verify quantity increments\n4. Check price calculation is correct',
                        'expected': 'Adding same product increases quantity and total price calculates correctly',
                        'test_data': 'Same product added 3 times'
                    }
                ]
            })
            
            features.append({
                'description': 'Shopping cart management operations',
                'test_cases': [
                    {
                        'steps': '1. Add multiple items to cart\n2. Navigate to cart page\n3. Update quantity of items\n4. Remove one or more items\n5. Verify cart total recalculates\n6. Check updated cart contents',
                        'expected': 'Cart allows quantity updates and item removal, totals recalculate correctly after each change',
                        'test_data': 'Multiple products with different quantities'
                    },
                    {
                        'steps': '1. Add items to cart\n2. Close browser\n3. Reopen browser and login\n4. Navigate to cart\n5. Verify cart items are persisted',
                        'expected': 'Cart items are saved and persist across sessions',
                        'test_data': 'Cart persistence test'
                    },
                    {
                        'steps': '1. Add items to cart\n2. Click "Clear Cart" or remove all items\n3. Verify cart is empty\n4. Check cart shows empty state message',
                        'expected': 'Cart can be cleared and shows appropriate empty state',
                        'test_data': 'Empty cart'
                    }
                ]
            })
            
            features.append({
                'description': 'Checkout process and order placement',
                'test_cases': [
                    {
                        'steps': '1. Add items to cart\n2. Click "Proceed to Checkout"\n3. Enter shipping address\n4. Select shipping method\n5. Enter payment information\n6. Review order\n7. Click "Place Order"\n8. Verify order confirmation',
                        'expected': 'Checkout process completes successfully, payment is processed, and order confirmation with order ID is displayed',
                        'test_data': 'Address: 123 Main St, Payment: Credit Card ending 1234'
                    },
                    {
                        'steps': '1. Proceed to checkout\n2. Apply discount/promo code\n3. Verify discount is applied\n4. Check total price is reduced\n5. Complete order',
                        'expected': 'Promo code applies discount correctly and final price reflects discount',
                        'test_data': 'Promo code: SAVE20'
                    },
                    {
                        'steps': '1. Add items to cart\n2. Proceed to checkout\n3. Select "Cash on Delivery" payment\n4. Complete order\n5. Verify order is placed without payment',
                        'expected': 'COD orders are placed successfully without immediate payment',
                        'test_data': 'Payment method: COD'
                    }
                ]
            })
            
            # Negative scenarios
            features.append({
                'description': 'Checkout with invalid or incomplete data',
                'test_cases': [
                    {
                        'steps': '1. Add items to cart\n2. Proceed to checkout\n3. Enter invalid payment details\n4. Attempt to complete transaction\n5. Verify error message\n6. Check order is not placed',
                        'expected': 'System displays payment error message and does not process transaction or create order',
                        'test_data': 'Invalid card number: 0000 0000 0000 0000'
                    },
                    {
                        'steps': '1. Proceed to checkout\n2. Leave required address fields empty\n3. Try to continue\n4. Verify validation errors',
                        'expected': 'System displays validation errors for required shipping address fields',
                        'test_data': 'Incomplete address'
                    },
                    {
                        'steps': '1. Add out-of-stock item to cart\n2. Proceed to checkout\n3. Verify system prevents checkout\n4. Check appropriate message is shown',
                        'expected': 'System prevents checkout of out-of-stock items with clear message',
                        'test_data': 'Out of stock product'
                    }
                ]
            })
            
            # Boundary scenarios
            features.append({
                'description': 'Cart quantity and price boundary testing',
                'test_cases': [
                    {
                        'steps': '1. Add product to cart\n2. Try to set quantity to 0\n3. Verify system behavior\n4. Check if item is removed or error shown',
                        'expected': 'System either removes item or shows minimum quantity error',
                        'test_data': 'Quantity: 0'
                    },
                    {
                        'steps': '1. Add product to cart\n2. Try to set quantity to maximum limit (999)\n3. Verify system accepts or shows limit\n4. Check price calculation',
                        'expected': 'System handles maximum quantity correctly or shows limit message',
                        'test_data': 'Quantity: 999'
                    },
                    {
                        'steps': '1. Add product to cart\n2. Enter negative quantity\n3. Verify system rejects invalid input',
                        'expected': 'System prevents negative quantities and shows validation error',
                        'test_data': 'Quantity: -5'
                    }
                ]
            })
            
            # Security scenarios
            features.append({
                'description': 'Payment security and data protection',
                'test_cases': [
                    {
                        'steps': '1. Proceed to payment page\n2. Enter credit card details\n3. Check if card number is masked\n4. Verify CVV is not stored\n5. Check SSL/HTTPS is used',
                        'expected': 'Payment page uses HTTPS, card details are masked, and sensitive data is not stored',
                        'test_data': 'Payment security check'
                    },
                    {
                        'steps': '1. Add items to cart\n2. Manipulate cart price in browser console\n3. Proceed to checkout\n4. Verify server validates actual price',
                        'expected': 'Server-side validation prevents price manipulation',
                        'test_data': 'Price manipulation attempt'
                    }
                ]
            })
            
            # Integration scenarios
            features.append({
                'description': 'Payment gateway integration',
                'test_cases': [
                    {
                        'steps': '1. Proceed to payment\n2. Select credit card payment\n3. Enter valid card details\n4. Submit payment\n5. Verify payment gateway processes\n6. Check order status updates',
                        'expected': 'Payment gateway integration works correctly and order status reflects payment',
                        'test_data': 'Test card: 4111 1111 1111 1111'
                    },
                    {
                        'steps': '1. Initiate payment\n2. Simulate payment gateway timeout\n3. Verify system handles timeout\n4. Check order status and user notification',
                        'expected': 'System handles payment gateway timeouts gracefully with appropriate messaging',
                        'test_data': 'Gateway timeout simulation'
                    }
                ]
            })
        
        elif category == 'navigation':
            features.append({
                'description': 'Navigation menu and page accessibility',
                'test_cases': [
                    {
                        'steps': '1. Open application home page\n2. Locate navigation menu\n3. Click on each menu item one by one\n4. Verify each page loads correctly\n5. Check breadcrumb navigation\n6. Test back button functionality',
                        'expected': 'All navigation links work correctly, pages load without errors, and breadcrumbs show correct path',
                        'test_data': 'Menu items: Home, Products, About, Contact'
                    },
                    {
                        'steps': '1. Navigate to any page\n2. Copy page URL\n3. Open new browser tab\n4. Paste and access URL directly\n5. Verify page loads correctly\n6. Check page state is maintained',
                        'expected': 'Direct URLs work correctly and load appropriate pages with correct content',
                        'test_data': 'Deep link URLs'
                    },
                    {
                        'steps': '1. Hover over navigation menu items\n2. Check for dropdown/submenu\n3. Click on submenu items\n4. Verify submenu navigation works\n5. Test nested menu levels if any',
                        'expected': 'Dropdown menus appear on hover, submenu items are clickable and navigate correctly',
                        'test_data': 'Menu with submenus'
                    }
                ]
            })
        
        elif category == 'reporting':
            features.append({
                'description': 'Report generation and export functionality',
                'test_cases': [
                    {
                        'steps': '1. Navigate to reports section\n2. Select report type from dropdown\n3. Set date range (start and end date)\n4. Apply filters if available\n5. Click "Generate Report" button\n6. Wait for report to load\n7. Verify report data accuracy',
                        'expected': 'Report is generated successfully with accurate data based on selected criteria and date range',
                        'test_data': 'Report type: Sales Report, Date: 01/01/2024 to 31/01/2024'
                    },
                    {
                        'steps': '1. Generate a report\n2. Click "Export" or "Download" button\n3. Select export format (PDF, Excel, or CSV)\n4. Click confirm\n5. Wait for download\n6. Open downloaded file\n7. Verify data integrity',
                        'expected': 'Report is exported in selected format with correct data and proper formatting',
                        'test_data': 'Export format: Excel (.xlsx)'
                    },
                    {
                        'steps': '1. Navigate to reports\n2. Try to generate report without selecting required parameters\n3. Click generate\n4. Verify validation message',
                        'expected': 'System displays validation error for missing required parameters',
                        'test_data': 'Missing date range'
                    }
                ]
            })
        
        elif category == 'validation':
            features.append({
                'description': 'Input validation and error handling',
                'test_cases': [
                    {
                        'steps': '1. Navigate to form page\n2. Enter invalid data in various fields (wrong format, special chars)\n3. Click submit button\n4. Verify validation messages appear\n5. Check field highlighting\n6. Verify form is not submitted',
                        'expected': 'System validates all fields, displays clear error messages, and highlights invalid fields',
                        'test_data': 'Invalid email: notanemail, Invalid phone: abc123'
                    },
                    {
                        'steps': '1. Open form\n2. Test field constraints (min/max length, numeric range)\n3. Enter values exceeding limits\n4. Verify real-time validation\n5. Check error message clarity',
                        'expected': 'Field constraints are enforced, validation occurs in real-time, and clear messages guide user',
                        'test_data': 'Text exceeding max length, Number outside range'
                    },
                    {
                        'steps': '1. Fill form with valid data after seeing errors\n2. Verify error messages disappear\n3. Submit form\n4. Verify successful submission',
                        'expected': 'Error messages clear when valid data is entered and form submits successfully',
                        'test_data': 'Corrected valid data'
                    }
                ]
            })
        
        elif category == 'configuration':
            features.append({
                'description': 'System settings and configuration management',
                'test_cases': [
                    {
                        'steps': '1. Login to application\n2. Navigate to settings/preferences page\n3. Modify configuration options (theme, language, notifications)\n4. Click save button\n5. Verify success message\n6. Refresh page\n7. Verify settings are applied',
                        'expected': 'Configuration changes are saved successfully and applied immediately across the application',
                        'test_data': 'Theme: Dark mode, Language: English, Notifications: Enabled'
                    },
                    {
                        'steps': '1. Change user settings\n2. Logout from application\n3. Login again\n4. Navigate to settings\n5. Verify settings persist across sessions',
                        'expected': 'User preferences are maintained across sessions and remain after logout/login',
                        'test_data': 'User preferences'
                    },
                    {
                        'steps': '1. Navigate to settings\n2. Click "Reset to Default" button\n3. Verify confirmation dialog\n4. Confirm reset\n5. Verify all settings return to default values',
                        'expected': 'Settings are reset to default values successfully',
                        'test_data': 'Default configuration'
                    }
                ]
            })
        
        return features
    
    def _generate_generic_tests(self, content):
        """Generate generic test cases when no specific features are detected"""
        features = []
        
        # Extract sentences or key phrases from content
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20][:10]
        
        if sentences:
            features.append({
                'description': 'Verify core functionality based on requirements',
                'test_cases': [
                    {
                        'steps': f'1. Review requirement: {sentences[0][:80]}...\n2. Set up test environment\n3. Execute functionality\n4. Verify expected behavior',
                        'expected': 'Functionality works as described in requirements',
                        'test_data': 'Test data based on requirements'
                    },
                    {
                        'steps': '1. Test with valid inputs\n2. Verify positive scenarios\n3. Check output correctness',
                        'expected': 'System processes valid inputs correctly',
                        'test_data': 'Valid test data'
                    },
                    {
                        'steps': '1. Test with invalid inputs\n2. Verify error handling\n3. Check error messages',
                        'expected': 'System handles invalid inputs gracefully with appropriate error messages',
                        'test_data': 'Invalid test data'
                    }
                ]
            })
        
        features.append({
            'description': 'Verify system usability and user interface',
            'test_cases': [
                {
                    'steps': '1. Navigate through the application\n2. Check UI elements are properly displayed\n3. Verify responsive design\n4. Test on different screen sizes',
                    'expected': 'UI is user-friendly and displays correctly on all devices',
                    'test_data': 'Different devices and browsers'
                },
                {
                    'steps': '1. Test all interactive elements (buttons, links, forms)\n2. Verify tooltips and help text\n3. Check accessibility features',
                    'expected': 'All interactive elements work correctly and are accessible',
                    'test_data': 'UI interaction'
                }
            ]
        })
        
        features.append({
            'description': 'Verify system performance and reliability',
            'test_cases': [
                {
                    'steps': '1. Measure page load times\n2. Test with multiple concurrent users\n3. Monitor system resources\n4. Verify response times',
                    'expected': 'System performs within acceptable response time limits',
                    'test_data': 'Performance metrics'
                },
                {
                    'steps': '1. Test system under load\n2. Verify stability\n3. Check for memory leaks\n4. Monitor error rates',
                    'expected': 'System remains stable under normal and peak load conditions',
                    'test_data': 'Load test scenarios'
                }
            ]
        })
        
        return features

