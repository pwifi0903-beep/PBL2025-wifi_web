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
        // 타임아웃 설정 (60초)
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('요청 시간이 초과되었습니다.')), 60000);
        });
        
        // API 요청과 타임아웃 경쟁
        Promise.race([
            fetchWithAuth('/api/expert/scan', {
                method: 'POST'
            }),
            timeoutPromise
        ])
        .then(response => {
            if (!response) {
                throw new Error('서버 응답이 없습니다.');
            }
            
            // HTTP 상태 코드 확인
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
                } else if (response.status >= 500) {
                    throw new Error('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
                } else {
                    throw new Error(`서버 오류 (${response.status})`);
                }
            }
            
            return response.json();
        })
        .then(data => {
            if (!data) {
                throw new Error('응답 데이터가 없습니다.');
            }
            
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
                const errorMsg = data.error || '알 수 없는 오류가 발생했습니다.';
                showError('스캔 중 오류가 발생했습니다: ' + errorMsg);
            }
        })
        .catch(error => {
            console.error('스캔 오류:', error);
            
            let errorMessage = '스캔 중 오류가 발생했습니다.';
            if (error.message) {
                if (error.message.includes('시간이 초과')) {
                    errorMessage = '스캔 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.';
                } else if (error.message.includes('네트워크') || error.message.includes('fetch')) {
                    errorMessage = '네트워크 연결을 확인해주세요.';
                } else if (error.message.includes('인증')) {
                    errorMessage = error.message;
                } else {
                    errorMessage = error.message;
                }
            }
            
            showError(errorMessage);
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
            const isNewData = wifi.is_new_data === true;
            // 실제 스캔이면 "실제 스캔" 배지, 신규 데이터면 배지 없음, 기존 더미면 "시뮬레이션" 배지
            let scanBadge = '';
            if (isRealScan) {
                scanBadge = '<span class="scan-badge">실제 스캔</span>';
            } else if (!isNewData) {
                scanBadge = '<span class="scan-badge dummy">시뮬레이션</span>';
            }
            
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
                    ${wifiData.protocol.toUpperCase() === 'WPA2' ? `
                    <button id="krackCheckBtn" class="btn btn-warning btn-large">
                        <span class="btn-icon">🔓</span>
                        KRACK 점검
                    </button>
                    ` : ''}
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
        
        // KRACK 점검 버튼 이벤트
        const krackCheckBtn = document.getElementById('krackCheckBtn');
        if (krackCheckBtn) {
            krackCheckBtn.addEventListener('click', function() {
                if (currentWifiData) {
                    performKrackCheck(currentWifiData);
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
        progressText.textContent = '점검을 시작합니다...';
        
        // 기존 polling 중지
        if (progressPollInterval) {
            clearInterval(progressPollInterval);
            progressPollInterval = null;
        }
        
        // 더미 데이터인지 확인
        const isRealScan = wifiData.is_real_scan === true;
        // 신규 데이터인지 확인 (SWU WiFi 등)
        const isNewData = wifiData.is_new_data === true;
        
        if (isRealScan) {
            // 실제 스캔 데이터인 경우 크래킹 시작
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
        } else if (isNewData) {
            // 신규 데이터인 경우 패킷 수집 시뮬레이션 (30초 동안 10-20%까지 진행 후 예상 시간 표시)
            performPacketCaptureSimulation(wifiData);
        } else {
            // 기존 더미 데이터인 경우 이전처럼 시뮬레이션 진행 애니메이션 (5초)
            const steps = [
                '1/4 보안 설정 확인 중...',
                '2/4 약한 암호화 확인 중...',
                '3/4 취약점 스캔 중...',
                '4/4 분석 완료 중...'
            ];
            
            let currentStep = 0;
            const stepInterval = setInterval(() => {
                if (currentStep < steps.length) {
                    progressFill.style.width = `${((currentStep + 1) / steps.length) * 100}%`;
                    progressText.textContent = steps[currentStep];
                    currentStep++;
                } else {
                    clearInterval(stepInterval);
                    
                    // 실제 보안 점검 API 호출
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
                        if (data.success) {
                            if (data.result) {
                                // 시뮬레이션 결과
                                showSecurityCheckResult(data.result);
                            } else {
                                showAlert('보안 점검 중 오류가 발생했습니다.', 'error');
                            }
                        } else {
                            showAlert('보안 점검 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showAlert('네트워크 오류가 발생했습니다.', 'error');
                    })
                    .finally(() => {
                        // 진행 표시 숨김
                        setTimeout(() => {
                            securityCheckProgress.style.display = 'none';
                        }, 2000);
                    });
                }
            }, 1250); // 5초 / 4단계 = 1.25초씩
        }
    }
    
    // 패킷 수집 시뮬레이션 (신규 데이터용 - 30초 동안 진행 후 예상 시간 표시)
    function performPacketCaptureSimulation(wifiData) {
        const captureSteps = [
            { message: '모니터 모드 전환 중...', progress: 2, duration: 2500 },
            { message: `채널 ${wifiData.channel || 6} 설정 중...`, progress: 4, duration: 2500 },
            { message: '패킷 수집 시작...', progress: 6, duration: 3000 },
            { message: '핸드셰이크 패킷 대기 중...', progress: 8, duration: 4000 },
            { message: '데이터 패킷 수집 중...', progress: 10, duration: 3500 },
            { message: '데이터 패킷 수집 중...', progress: 12, duration: 3500 },
            { message: '데이터 패킷 수집 중...', progress: 14, duration: 4000 },
            { message: '데이터 패킷 수집 중...', progress: 16, duration: 4000 },
            { message: '데이터 패킷 수집 중...', progress: 18, duration: 4000 },
            { message: '핸드셰이크 캡처 대기 중... (클라이언트 연결 필요)', progress: 20, duration: 4000 }
        ];
        
        let stepIndex = 0;
        
        function runStep() {
            if (stepIndex < captureSteps.length) {
                const step = captureSteps[stepIndex];
                progressFill.style.width = `${step.progress}%`;
                progressText.textContent = step.message;
                stepIndex++;
                setTimeout(runStep, step.duration);
            } else {
                // 30초 후 예상 시간 표시하고 진행 중 상태 유지
                progressFill.style.width = '20%';
                progressText.innerHTML = `
                    <div class="long-process-info">
                        <div class="process-status">패킷 수집 진행 중...</div>
                        <div class="process-estimate">패킷 수집 속도에 따라 <strong>최소 3시간</strong>에서 수시간 이상 소요될 수 있습니다.</div>
                        <button class="btn btn-small btn-cancel" onclick="cancelSecurityCheck()">취소</button>
                    </div>
                `;
            }
        }
        
        runStep();
    }
    
    // 보안 점검 취소
    window.cancelSecurityCheck = function() {
        if (progressPollInterval) {
            clearInterval(progressPollInterval);
            progressPollInterval = null;
        }
        securityCheckProgress.style.display = 'none';
        showAlert('보안 점검이 취소되었습니다.', 'warning');
    };
    
    // KRACK 점검 수행
    function performKrackCheck(wifiData) {
        if (wifiData.protocol.toUpperCase() !== 'WPA2') {
            showAlert('KRACK 점검은 WPA2 네트워크에서만 수행할 수 있습니다.', 'warning');
            return;
        }
        
        // 진행 표시 시작
        securityCheckProgress.style.display = 'flex';
        progressFill.style.width = '0%';
        progressText.textContent = 'KRACK 취약점 점검을 시작합니다...';
        
        // 신규 데이터인지 확인
        const isNewData = wifiData.is_new_data === true;
        
        if (isNewData) {
            // 신규 데이터인 경우 30초 동안 진행 후 예상 시간 표시
            performKrackSimulationLong(wifiData);
        } else {
            // 기존 더미 데이터인 경우 5초 내 결과 표시
            performKrackSimulationShort(wifiData);
        }
    }
    
    // KRACK 점검 시뮬레이션 (기존 데이터용 - 5초)
    function performKrackSimulationShort(wifiData) {
        const steps = [
            { message: '1/4 KRACK 취약점 스캔 준비 중...', progress: 25 },
            { message: '2/4 4-way 핸드셰이크 분석 중...', progress: 50 },
            { message: '3/4 키 재설치 공격 테스트 중...', progress: 75 },
            { message: '4/4 분석 완료 중...', progress: 100 }
        ];
        
        let currentStep = 0;
        const stepInterval = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                progressFill.style.width = `${step.progress}%`;
                progressText.textContent = step.message;
                currentStep++;
            } else {
                clearInterval(stepInterval);
                
                // KRACK 점검 API 호출
                fetchWithAuth('/api/expert/krack-check', {
                    method: 'POST',
                    body: JSON.stringify({
                        wifi_data: wifiData,
                        ssid: wifiData.ssid
                    })
                })
                .then(response => {
                    if (!response) return null;
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        showKrackResult(data.result, wifiData);
                    } else {
                        showAlert('KRACK 점검 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('네트워크 오류가 발생했습니다.', 'error');
                })
                .finally(() => {
                    setTimeout(() => {
                        securityCheckProgress.style.display = 'none';
                    }, 2000);
                });
            }
        }, 1250); // 5초 / 4단계 = 1.25초씩
    }
    
    // KRACK 점검 시뮬레이션 (신규 데이터용 - 30초 후 예상 시간 표시)
    function performKrackSimulationLong(wifiData) {
        const krackSteps = [
            { message: 'KRACK 점검 준비 중...', progress: 2, duration: 2000 },
            { message: '모니터 모드 전환 중...', progress: 4, duration: 2000 },
            { message: `타겟 AP 설정 중... (${wifiData.ssid})`, progress: 6, duration: 2000 },
            { message: '4-way 핸드셰이크 캡처 대기 중...', progress: 8, duration: 4000 },
            { message: 'PTK 재설치 테스트 준비 중...', progress: 10, duration: 3000 },
            { message: '키 재설치 공격 시뮬레이션 중...', progress: 12, duration: 4000 },
            { message: 'GTK 재설치 테스트 중...', progress: 14, duration: 4000 },
            { message: 'IGTK 재설치 테스트 중...', progress: 16, duration: 3000 },
            { message: '추가 핸드셰이크 수집 중...', progress: 18, duration: 3000 },
            { message: '취약점 분석 중...', progress: 20, duration: 3000 }
        ];
        
        let stepIndex = 0;
        
        function runStep() {
            if (stepIndex < krackSteps.length) {
                const step = krackSteps[stepIndex];
                progressFill.style.width = `${step.progress}%`;
                progressText.textContent = step.message;
                stepIndex++;
                setTimeout(runStep, step.duration);
            } else {
                // 30초 후 예상 시간 표시하고 진행 중 상태 유지
                progressFill.style.width = '20%';
                progressText.innerHTML = `
                    <div class="long-process-info">
                        <div class="process-status">KRACK 취약점 점검 진행 중...</div>
                        <div class="process-estimate">패킷 수집 속도에 따라 <strong>최소 3시간</strong>에서 수시간 이상 소요될 수 있습니다.</div>
                        <button class="btn btn-small btn-cancel" onclick="cancelSecurityCheck()">취소</button>
                    </div>
                `;
            }
        }
        
        runStep();
    }
    
    // KRACK 점검 결과 표시
    function showKrackResult(result, wifiData) {
        const isVulnerable = result.vulnerable;
        
        // WiFi 데이터에 KRACK 점검 상태 저장
        if (currentWifiData) {
            currentWifiData.krack_checked = true;
            currentWifiData.krack_vulnerable = isVulnerable;
        }
        
        // WiFi 목록 업데이트
        updateWifiListKrackStatus();
        
        if (isVulnerable) {
            showAlert(`⚠️ KRACK 취약점 발견!\n\nSSID: ${wifiData.ssid}\n\n이 네트워크는 KRACK(Key Reinstallation Attack) 공격에 취약합니다.\n\n권고사항:\n• 라우터 펌웨어 업데이트 필요\n• WPA3로 업그레이드 권고\n• 패치가 적용될 때까지 민감한 작업 자제`, 'error');
        } else {
            showAlert(`✅ KRACK 취약점 없음\n\nSSID: ${wifiData.ssid}\n\n이 네트워크는 KRACK 공격에 대해 안전합니다.\n\n펌웨어가 최신 상태이거나 패치가 적용되어 있습니다.`, 'success');
        }
    }
    
    // WiFi 목록에서 KRACK 상태 업데이트
    function updateWifiListKrackStatus() {
        const wifiItems = document.querySelectorAll('.wifi-item-expert');
        wifiItems.forEach(item => {
            const index = parseInt(item.dataset.index);
            if (wifiDataList[index] && currentWifiData && 
                wifiDataList[index].ssid === currentWifiData.ssid &&
                wifiDataList[index].bssid === currentWifiData.bssid) {
                wifiDataList[index].krack_checked = currentWifiData.krack_checked;
                wifiDataList[index].krack_vulnerable = currentWifiData.krack_vulnerable;
            }
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
