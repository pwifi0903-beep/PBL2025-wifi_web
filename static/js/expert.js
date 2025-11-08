// 관리자용 페이지 JavaScript

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
    logoutBtn.addEventListener('click', function() {
        if (confirm('정말 로그아웃하시겠습니까?')) {
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
        fetch('/api/expert/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                wifiDataList = data.wifi_list;
                displayWifiList(data.wifi_list);
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
        
        const wifiHTML = wifiDataArray.map((wifi, index) => `
            <div class="wifi-item-expert" data-index="${index}">
                <div class="wifi-info-expert">
                    <div class="wifi-name-expert">${escapeHtml(wifi.ssid)}</div>
                </div>
                <div class="wifi-status-expert">
                    <span class="security-level ${wifi.security_level}">
                        ${getSecurityLevelText(wifi.security_level)}
                    </span>
                </div>
            </div>
        `).join('');
        
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
                    <ul class="detail-attack-vectors">
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
    
    function performSecurityCheck(wifiData) {
        if (wifiData.protocol.toLowerCase() === 'open') {
            showAlert('Open 네트워크는 보안 점검을 수행할 수 없습니다.', 'warning');
            return;
        }
        
        // 진행 표시 시작
        securityCheckProgress.style.display = 'flex';
        progressFill.style.width = '0%';
        progressText.textContent = '점검을 시작합니다...';
        
        // 4단계 진행 시뮬레이션
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
                fetch('/api/expert/security-check', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        protocol: wifiData.protocol
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showSecurityCheckResult(data.result);
                    } else {
                        showAlert('보안 점검 중 오류가 발생했습니다: ' + data.error, 'error');
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
    
    function showSecurityCheckResult(result) {
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
            showAlert(`보안 점검 완료!\n\n권고사항:\n• ${recommendations}`, 'success');
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
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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
