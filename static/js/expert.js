// 관리자용 페이지 JavaScript

// JWT 토큰 관리 함수
function getAccessToken() {
    // localStorage에서 토큰 가져오기
    return localStorage.getItem('access_token');
}

function getRefreshToken() {
    // localStorage에서 Refresh Token 가져오기
    return localStorage.getItem('refresh_token');
}

function setAccessToken(token) {
    // Access Token 저장
    localStorage.setItem('access_token', token);
}

function clearTokens() {
    // 모든 토큰 삭제
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
}

function getAuthHeaders() {
    // Authorization 헤더 생성
    const token = getAccessToken();
    const headers = {
        'Content-Type': 'application/json',
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
}

async function refreshAccessToken() {
    // Refresh Token으로 Access Token 갱신
    const refreshToken = getRefreshToken();
    
    if (!refreshToken) {
        return false;
    }
    
    try {
        const response = await fetch('/api/expert/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${refreshToken}`
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.access_token) {
            setAccessToken(data.access_token);
            return true;
        }
    } catch (error) {
        console.error('Token refresh error:', error);
    }
    
    return false;
}

async function fetchWithAuth(url, options = {}) {
    // 인증이 포함된 fetch 요청
    const authHeaders = getAuthHeaders();
    
    // 기존 헤더와 병합
    const headers = options.headers ? { ...authHeaders, ...options.headers } : authHeaders;
    options.headers = headers;
    
    let response = await fetch(url, options);
    
    // 401 응답 시 토큰 갱신 시도
    if (response.status === 401) {
        const refreshed = await refreshAccessToken();
        
        if (refreshed) {
            // 토큰 갱신 성공 - 재요청
            const newAuthHeaders = getAuthHeaders();
            const newHeaders = options.headers ? { ...newAuthHeaders, ...options.headers } : newAuthHeaders;
            options.headers = newHeaders;
            response = await fetch(url, options);
        } else {
            // 토큰 갱신 실패 - 로그인 페이지로 리다이렉트
            clearTokens();
            window.location.href = '/expert/login';
            return null;
        }
    }
    
    return response;
}

document.addEventListener('DOMContentLoaded', function() {
    const scanBtn = document.getElementById('scanBtn');
    const wifiList = document.getElementById('wifiList');
    const wifiCount = document.getElementById('wifiCount');
    const securityCheckProgress = document.getElementById('securityCheckProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const logoutBtn = document.getElementById('logoutBtn');
    
    let isScanning = false;
    let currentWifiData = null;
    let wifiDataList = [];
    
    // 로그아웃 버튼 클릭 이벤트
    logoutBtn.addEventListener('click', async function() {
        if (confirm('정말 로그아웃하시겠습니까?')) {
            // 로그아웃 API 호출
            try {
                await fetchWithAuth('/expert/logout', {
                    method: 'POST'
                });
            } catch (error) {
                console.error('Logout error:', error);
            }
            
            // 토큰 삭제 및 로그인 페이지로 이동
            clearTokens();
            window.location.href = '/expert/login';
        }
    });
    
    // 스캔 버튼 클릭 이벤트
    scanBtn.addEventListener('click', function() {
        if (isScanning) return;
        startScan();
    });
    
    function startScan() {
        isScanning = true;
        
        // 버튼 상태 변경
        scanBtn.classList.add('scan-loading');
        scanBtn.innerHTML = '<span class="btn-icon">⏳</span> 스캔 중...';
        scanBtn.disabled = true;
        
        // 로딩 애니메이션 표시
        showScanningAnimation();
        
        // 5초 후 실제 스캔 실행
        setTimeout(() => {
            performScan();
        }, 5000);
    }
    
    function showScanningAnimation() {
        wifiList.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <div class="loading-text">근처 와이파이들을 상세 스캔합니다...</div>
            </div>
        `;
        wifiCount.textContent = '스캔 중...';
    }
    
    function performScan() {
        fetchWithAuth('/api/expert/scan', {
            method: 'POST'
        })
        .then(response => {
            if (!response) return null;
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // OPEN 프로토콜인 경우 자동으로 취약 상태로 설정
                wifiDataList = data.wifi_list.map(wifi => {
                    if (wifi.protocol && wifi.protocol.toUpperCase() === 'OPEN') {
                        wifi.check_status = 'vulnerable';
                    }
                    return wifi;
                });
                displayWifiList(wifiDataList);
                wifiCount.textContent = `${data.count}개의 와이파이 발견`;
            } else {
                showError('스캔 중 오류가 발생했습니다: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('네트워크 오류가 발생했습니다.');
        })
        .finally(() => {
            resetScanButton();
        });
    }
    
    function displayWifiList(wifiDataArray) {
        if (wifiDataArray.length === 0) {
            document.getElementById('wifiList').innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <h3>와이파이를 찾을 수 없습니다</h3>
                    <p>주변에 와이파이 네트워크가 없거나 스캔에 실패했습니다.</p>
                </div>
            `;
            return;
        }
        
        // 같은 SSID를 가진 WiFi 그룹화
        const ssidGroups = {};
        wifiDataArray.forEach(wifi => {
            if (!ssidGroups[wifi.ssid]) {
                ssidGroups[wifi.ssid] = [];
            }
            ssidGroups[wifi.ssid].push(wifi);
        });
        
        // Rogue AP 탐지: 같은 SSID 중 OPEN 프로토콜이 있는지 확인
        const rogueApSsids = new Set();
        Object.keys(ssidGroups).forEach(ssid => {
            const group = ssidGroups[ssid];
            if (group.length > 1) {
                const hasOpen = group.some(wifi => wifi.protocol && wifi.protocol.toUpperCase() === 'OPEN');
                if (hasOpen) {
                    rogueApSsids.add(ssid);
                }
            }
        });
        
        const wifiHTML = wifiDataArray.map((wifi, index) => {
            // 취약 점검 상태 확인
            // OPEN 프로토콜인 경우 자동으로 취약으로 표시
            let checkStatus = wifi.check_status || 'unchecked';
            if (wifi.protocol && wifi.protocol.toUpperCase() === 'OPEN') {
                checkStatus = 'vulnerable';
            }
            const checkStatusText = getCheckStatusText(checkStatus);
            const checkStatusClass = checkStatus;
            
            // Rogue AP 확인
            const isRogueAp = rogueApSsids.has(wifi.ssid) && wifi.protocol && wifi.protocol.toUpperCase() === 'OPEN';
            
            // 실제 스캔 데이터인지 확인
            const isRealScan = wifi.is_real_scan === true;
            const scanBadge = isRealScan ? '<span class="scan-badge">실제 스캔</span>' : '<span class="scan-badge dummy">시뮬레이션</span>';
            
            return `
            <div class="wifi-item-expert" data-index="${index}">
                <div class="wifi-info-expert">
                    <div class="wifi-name-expert">
                        ${escapeHtml(wifi.ssid)}
                        ${scanBadge}
                    </div>
                    ${isRogueAp ? '<div class="rogue-warning">⚠️ Rogue AP 의심</div>' : ''}
                </div>
                <div class="wifi-status-expert">
                    <div class="status-item">
                        <span class="status-label">프로토콜 위험도:</span>
                        <span class="security-level ${wifi.security_level}">
                            ${getSecurityLevelText(wifi.security_level)}
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">점검 결과:</span>
                        <span class="check-status ${checkStatusClass}">
                            ${checkStatusText}
                        </span>
                    </div>
                </div>
            </div>
        `;
        }).join('');
        
        document.getElementById('wifiList').innerHTML = wifiHTML;
        
        // 클릭 이벤트 추가
        const wifiItems = document.getElementById('wifiList').querySelectorAll('.wifi-item-expert');
        wifiItems.forEach(item => {
            item.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                // 선택된 아이템 표시
                wifiItems.forEach(wifiItem => wifiItem.classList.remove('selected'));
                this.classList.add('selected');
                showWifiDetail(wifiDataArray[index]);
            });
        });
        
        // 애니메이션 효과
        wifiItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    function showWifiDetail(wifiData) {
        currentWifiData = wifiData;
        const wifiDetail = document.getElementById('wifiDetail');
        
        // 보안 가이드 정보 찾기
        const guideInfo = findSecurityGuideInfo(wifiData.protocol, wifiData.security_level);
        
        // 프로토콜 태그 생성
        const protocolTags = guideInfo ? guideInfo.protocols.map(protocol => 
            `<span class="protocol-tag">${protocol}</span>`
        ).join('') : '';
        
        // 공격 벡터 리스트 생성
        const attackVectorsList = guideInfo && guideInfo.attack_vectors && guideInfo.attack_vectors.length > 0 ? 
            guideInfo.attack_vectors.map(attack => `<li>${escapeHtml(attack)}</li>`).join('') : 
            (wifiData.vulnerabilities && wifiData.vulnerabilities.length > 0 ?
                wifiData.vulnerabilities.map(vuln => `<li>${escapeHtml(vuln)}</li>`).join('') :
                '<li>알려진 취약점이 없습니다.</li>');
        
        // 권고사항 리스트 생성
        const recommendationsList = guideInfo && guideInfo.recommendations ? 
            guideInfo.recommendations.map(rec => `<li>${escapeHtml(rec)}</li>`).join('') : '';
        
        wifiDetail.innerHTML = `
            <div class="wifi-detail-content">
                <div class="detail-header">
                    <h2>${escapeHtml(wifiData.ssid)}</h2>
                    <span class="security-level ${wifiData.security_level}">
                        ${getSecurityLevelText(wifiData.security_level)}
                    </span>
                </div>
                
                <div class="detail-section">
                    <h3>기본 정보</h3>
                    <div class="detail-info-grid">
                        <div class="detail-info-item">
                            <label>BSSID:</label>
                            <span>${escapeHtml(wifiData.bssid)}</span>
                        </div>
                        <div class="detail-info-item">
                            <label>프로토콜:</label>
                            <span>${escapeHtml(wifiData.protocol)}</span>
                        </div>
                        <div class="detail-info-item">
                            <label>채널:</label>
                            <span>${escapeHtml(wifiData.channel)}</span>
                        </div>
                        <div class="detail-info-item">
                            <label>암호화:</label>
                            <span>${escapeHtml(wifiData.encryption)}</span>
                        </div>
                        <div class="detail-info-item">
                            <label>신호 강도:</label>
                            <span>${wifiData.signal_strength} dBm</span>
                        </div>
                        <div class="detail-info-item">
                            <label>보안 수준:</label>
                            <span class="security-level ${wifiData.security_level}">
                                ${getSecurityLevelText(wifiData.security_level)}
                            </span>
                        </div>
                    </div>
                </div>
                
                ${guideInfo ? `
                <div class="detail-section">
                    <h3>보안 설명</h3>
                    <p class="detail-description">${escapeHtml(guideInfo.description)}</p>
                </div>
                
                <div class="detail-section">
                    <h3>해당 프로토콜</h3>
                    <div class="protocol-tags">
                        ${protocolTags}
                    </div>
                </div>
                ` : ''}
                
                <div class="detail-section">
                    <h3>취약점 및 공격 벡터</h3>
                    <ul id="detailVulnList" class="detail-attack-vectors">
                        ${attackVectorsList}
                    </ul>
                </div>
                
                ${guideInfo ? `
                <div class="detail-section">
                    <h3>관리자 권고사항</h3>
                    <ul class="detail-recommendations">
                        ${recommendationsList}
                    </ul>
                </div>
                ` : ''}
                
                <div class="detail-actions">
                    <button id="securityCheckBtn" class="btn btn-danger btn-large ${wifiData.protocol.toLowerCase() === 'open' ? 'hidden' : ''}">
                        <span class="btn-icon">🛡️</span>
                        보안 점검
                    </button>
                    <button id="confirmBtn" class="btn btn-safe btn-large">
                        <span class="btn-icon">✅</span>
                        확인
                    </button>
                </div>
            </div>
        `;
        
        // 보안 점검 버튼 이벤트
        const securityCheckBtn = document.getElementById('securityCheckBtn');
        if (securityCheckBtn) {
            securityCheckBtn.addEventListener('click', function() {
                if (currentWifiData) {
                    performSecurityCheck(currentWifiData);
                }
            });
        }
        
        // 확인 버튼 이벤트
        const confirmBtn = document.getElementById('confirmBtn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', function() {
                // 선택 해제
                document.querySelectorAll('.wifi-item-expert').forEach(item => {
                    item.classList.remove('selected');
                });
                currentWifiData = null;
                
                // 초기 상태로 복원
                wifiDetail.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📋</div>
                        <h3>와이파이를 선택하세요</h3>
                        <p>왼쪽 목록에서 와이파이를 선택하면 상세 정보가 표시됩니다.</p>
                    </div>
                `;
            });
        }
    }
    
    // 보안 가이드 정보 찾기
    function findSecurityGuideInfo(protocol, securityLevel) {
        if (!securityGuideData) return null;
        
        // 프로토콜을 기반으로 보안 레벨 매핑
        const protocolMap = {
            'OPEN': 'critical',
            'WEP': 'danger',
            'WPA': 'warning',
            'WPA2': 'safe',
            'WPA2_WPS': 'danger',
            'WPA3': 'safe'
        };
        
        // 프로토콜을 기반으로 레벨 찾기
        let level = protocolMap[protocol.toUpperCase()];
        
        // 프로토콜이 매핑에 없으면 securityLevel 사용
        if (!level) {
            level = securityLevel;
        }
        
        return securityGuideData[level] || null;
    }
    
    let currentCrackingId = null;
    let progressPollInterval = null;
    
    function performSecurityCheck(wifiData) {
        if (wifiData.protocol.toLowerCase() === 'open') {
            showAlert('Open 네트워크는 보안 점검을 수행할 수 없습니다.', 'warning');
            return;
        }
        
        // 진행 표시 시작
        securityCheckProgress.style.display = 'flex';
        progressFill.style.width = '0%';
        progressText.textContent = '크래킹을 시작합니다...';
        
        // 기존 polling 중지
        if (progressPollInterval) {
            clearInterval(progressPollInterval);
            progressPollInterval = null;
        }
        
        // 크래킹 시작 API 호출
        fetchWithAuth('/api/expert/security-check', {
            method: 'POST',
            body: JSON.stringify({
                wifi_data: wifiData,
                protocol: wifiData.protocol
            })
        })
        .then(response => {
            if (!response) return null;
            return response.json();
        })
        .then(data => {
            if (data.success && data.cracking_id) {
                // 크래킹 ID 저장
                currentCrackingId = data.cracking_id;
                
                // 실시간 진행 상황 polling 시작
                startProgressPolling(currentCrackingId);
            } else if (data.success && data.result) {
                // 시뮬레이션 결과인 경우 (WiFi 데이터 없음)
                showSecurityCheckResult(data.result);
                securityCheckProgress.style.display = 'none';
            } else {
                showAlert('보안 점검 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
                securityCheckProgress.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('네트워크 오류가 발생했습니다.', 'error');
            securityCheckProgress.style.display = 'none';
        });
    }
    
    function startProgressPolling(crackingId) {
        // 즉시 한 번 조회
        checkCrackingProgress(crackingId);
        
        // 2초마다 진행 상황 조회
        progressPollInterval = setInterval(() => {
            checkCrackingProgress(crackingId);
        }, 2000);
    }
    
    function checkCrackingProgress(crackingId) {
        fetchWithAuth(`/api/expert/cracking-progress?cracking_id=${crackingId}`, {
            method: 'GET'
        })
        .then(response => {
            if (!response) return null;
            return response.json();
        })
        .then(data => {
            if (data.success && data.progress) {
                const progress = data.progress;
                
                // 진행률 업데이트
                progressFill.style.width = `${progress.progress || 0}%`;
                progressText.textContent = progress.message || '진행 중...';
                
                // 크래킹 상태 확인
                if (progress.status === 'completed') {
                    // 크래킹 완료
                    clearInterval(progressPollInterval);
                    progressPollInterval = null;
                    
                    // 결과 표시
                    if (data.result && data.result.success) {
                        const password = data.result.password || '알 수 없음';
                        showAlert(`크래킹 성공!\n\n패스워드: ${password}\n\n방법: ${data.result.method || '알 수 없음'}`, 'success');
                        
                        // WiFi 데이터 업데이트
                        if (currentWifiData) {
                            currentWifiData.check_status = 'vulnerable';
                            currentWifiData.cracked_password = password;
                            updateWifiListStatus();
                        }
                    } else {
                        showAlert('크래킹이 완료되었지만 패스워드를 찾지 못했습니다.', 'warning');
                    }
                    
                    // 진행 표시 숨김
                    setTimeout(() => {
                        securityCheckProgress.style.display = 'none';
                    }, 2000);
                    
                } else if (progress.status === 'failed' || progress.status === 'error') {
                    // 크래킹 실패
                    clearInterval(progressPollInterval);
                    progressPollInterval = null;
                    
                    showAlert(`크래킹 실패: ${progress.message || '알 수 없는 오류'}`, 'error');
                    
                    // 진행 표시 숨김
                    setTimeout(() => {
                        securityCheckProgress.style.display = 'none';
                    }, 2000);
                }
                // 'running' 상태는 계속 진행
            } else {
                console.error('진행 상황 조회 실패:', data.error);
            }
        })
        .catch(error => {
            console.error('진행 상황 조회 오류:', error);
        });
    }
    
    function updateWifiListStatus() {
        // WiFi 목록에서 해당 항목 찾아서 업데이트
        const wifiItems = document.querySelectorAll('.wifi-item-expert');
        wifiItems.forEach(item => {
            const index = parseInt(item.dataset.index);
            if (wifiDataList[index] && currentWifiData && wifiDataList[index].ssid === currentWifiData.ssid) {
                wifiDataList[index].check_status = currentWifiData.check_status;
                wifiDataList[index].cracked_password = currentWifiData.cracked_password;
                
                // 점검 결과 칸 업데이트
                const checkStatusElement = item.querySelector('.check-status');
                if (checkStatusElement) {
                    checkStatusElement.className = `check-status ${currentWifiData.check_status}`;
                    checkStatusElement.textContent = getCheckStatusText(currentWifiData.check_status);
                }
            }
        });
    }
    
    function showSecurityCheckResult(result) {
        if (!currentWifiData) return;
        
        // 점검 결과에 따라 취약 여부 판단
        // risk_level이 'danger' 또는 'warning'이면 취약, 'safe'면 안전
        const isVulnerable = result.risk_level === 'danger' || 
                            result.risk_level === 'warning' || 
                            result.risk_level === 'critical';
        
        // WiFi 데이터에 점검 상태 저장
        currentWifiData.check_status = isVulnerable ? 'vulnerable' : 'safe';
        
        // WiFi 목록에서 해당 항목 찾아서 업데이트
        const wifiItems = document.querySelectorAll('.wifi-item-expert');
        wifiItems.forEach(item => {
            const index = parseInt(item.dataset.index);
            if (wifiDataList[index] && wifiDataList[index].ssid === currentWifiData.ssid) {
                wifiDataList[index].check_status = currentWifiData.check_status;
                
                // 점검 결과 칸 업데이트
                const checkStatusElement = item.querySelector('.check-status');
                if (checkStatusElement) {
                    checkStatusElement.className = `check-status ${currentWifiData.check_status}`;
                    checkStatusElement.textContent = getCheckStatusText(currentWifiData.check_status);
                }
            }
        });
        
        // 취약점 목록 업데이트
        const vulnList = document.getElementById('detailVulnList');
        if (result.vulnerabilities && result.vulnerabilities.length > 0) {
            vulnList.innerHTML = result.vulnerabilities.map(vuln => 
                `<li>${escapeHtml(vuln)}</li>`
            ).join('');
        } else {
            vulnList.innerHTML = '<li>알려진 취약점이 없습니다.</li>';
        }
        
        // 권고사항 표시
        if (result.recommendations && result.recommendations.length > 0) {
            const recommendations = result.recommendations.join('\n• ');
            showAlert('보안 점검 완료!\n\n권고사항:\n• ' + recommendations, 'success');
        } else {
            showAlert('보안 점검이 완료되었습니다.', 'success');
        }
    }
    
    function resetScanButton() {
        isScanning = false;
        scanBtn.classList.remove('scan-loading');
        scanBtn.innerHTML = '<span class="btn-icon">🔍</span> 관리자용 스캔';
        scanBtn.disabled = false;
    }
    
    function showError(message) {
        wifiList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">❌</div>
                <h3>오류 발생</h3>
                <p>${message}</p>
            </div>
        `;
        wifiCount.textContent = '스캔 실패';
    }
    
    function getSecurityLevelText(level) {
        const levelTexts = {
            'critical': '매우 위험',
            'danger': '위험',
            'warning': '경고',
            'safe': '안전'
        };
        return levelTexts[level] || '알 수 없음';
    }
    
    function getCheckStatusText(status) {
        const statusTexts = {
            'vulnerable': '취약',
            'safe': '안전',
            'unchecked': '미점검'
        };
        return statusTexts[status] || '미점검';
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function showAlert(message, type) {
        // Popup 창으로 표시
        const popup = document.getElementById('resultPopup');
        const popupTitle = document.getElementById('popupTitle');
        const popupMessage = document.getElementById('popupMessage');
        const popupCloseBtn = document.getElementById('popupCloseBtn');
        const popupConfirmBtn = document.getElementById('popupConfirmBtn');
        
        // 제목 설정
        const titles = {
            'success': '✅ 보안 점검 완료',
            'error': '❌ 오류 발생',
            'warning': '⚠️ 경고'
        };
        popupTitle.textContent = titles[type] || '알림';
        
        // 메시지 설정 (줄바꿈 처리)
        popupMessage.innerHTML = message.replace(/\n/g, '<br>');
        
        // Popup 표시
        popup.style.display = 'flex';
        
        // 닫기 버튼 이벤트
        const closePopup = () => {
            popup.style.display = 'none';
        };
        
        popupCloseBtn.onclick = closePopup;
        popupConfirmBtn.onclick = closePopup;
        
        // 배경 클릭 시 닫기
        popup.querySelector('.popup-overlay').onclick = closePopup;
    }
    
    // 페이지 로드 시 초기 상태 설정
    wifiCount.textContent = '스캔을 시작하세요';
    
    // 아코디언 기능 초기화
    initAccordion();
});

// 아코디언 기능
function initAccordion() {
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    
    accordionHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const accordionItem = this.closest('.accordion-item');
            const accordionPanel = document.getElementById(targetId);
            
            // 현재 아코디언이 활성화되어 있는지 확인
            const isActive = accordionItem.classList.contains('active');
            
            // 모든 아코디언 닫기
            document.querySelectorAll('.accordion-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // 클릭된 아코디언이 비활성화 상태였다면 열기
            if (!isActive) {
                accordionItem.classList.add('active');
            }
        });
    });
}
