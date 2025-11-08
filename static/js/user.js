// 사용자용 페이지 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const scanBtn = document.getElementById('scanBtn');
    const wifiList = document.getElementById('wifiList');
    const wifiCount = document.getElementById('wifiCount');
    
    let isScanning = false;
    
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
                <div class="loading-text">근처 와이파이들을 스캔합니다...</div>
            </div>
        `;
        wifiCount.textContent = '스캔 중...';
    }
    
    function performScan() {
        fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
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
                    <div class="empty-icon">📶</div>
                    <h3>와이파이를 찾을 수 없습니다</h3>
                    <p>주변에 와이파이 네트워크가 없거나 스캔에 실패했습니다.</p>
                </div>
            `;
            return;
        }
        
        const wifiHTML = wifiDataArray.map((wifi, index) => `
            <div class="wifi-item-user" data-index="${index}">
                <div class="wifi-info-user">
                    <div class="wifi-name-user">${escapeHtml(wifi.ssid)}</div>
                    <div class="wifi-protocol-user">프로토콜: ${wifi.protocol}</div>
                </div>
                <div class="wifi-status-user">
                    <span class="security-level ${wifi.security_level}">
                        ${getSecurityLevelText(wifi.security_level)}
                    </span>
                </div>
            </div>
        `).join('');
        
        document.getElementById('wifiList').innerHTML = wifiHTML;
        
        // 클릭 이벤트 추가
        const wifiItems = document.getElementById('wifiList').querySelectorAll('.wifi-item-user');
        wifiItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
            
            // 클릭 이벤트 핸들러
            item.addEventListener('click', function() {
                // 선택된 아이템 표시
                wifiItems.forEach(wifiItem => wifiItem.classList.remove('selected'));
                this.classList.add('selected');
                showWifiDetail(wifiDataArray[index]);
            });
        });
        
        // 와이파이 데이터 저장
        window.wifiDataList = wifiDataArray;
    }
    
    function resetScanButton() {
        isScanning = false;
        scanBtn.classList.remove('scan-loading');
        scanBtn.innerHTML = '<span class="btn-icon">📶</span> 와이파이 스캔';
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
    
    // 페이지 로드 시 초기 상태 설정
    wifiCount.textContent = '스캔을 시작하세요';
});

// 보안 수준 텍스트 변환 함수 (전역 스코프)
function getSecurityLevelText(level) {
    const levelTexts = {
        'critical': '매우 위험',
        'danger': '위험',
        'warning': '경고',
        'safe': '안전'
    };
    return levelTexts[level] || '알 수 없음';
}

// HTML 이스케이프 함수 (전역 스코프)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 와이파이 상세 정보 표시
function showWifiDetail(wifiData) {
    const wifiDetail = document.getElementById('wifiDetail');
    
    if (!wifiDetail) {
        console.error('wifiDetail 요소를 찾을 수 없습니다.');
        return;
    }
    
    // 보안 가이드 정보 찾기
    const guideInfo = findSecurityGuideInfo(wifiData.protocol, wifiData.security_level);
    
    // 암호화 여부 판단
    const hasEncryption = wifiData.protocol.toUpperCase() !== 'OPEN';
    const encryptionStatus = hasEncryption ? '있음' : '없음';
    
    // 권고사항 리스트 생성
    const recommendationsList = guideInfo && guideInfo.recommendations ? 
        guideInfo.recommendations.map(rec => `<li>${escapeHtml(rec)}</li>`).join('') : '';
    
    wifiDetail.innerHTML = `
        <div class="wifi-detail-content">
            <div class="detail-header">
                <h2>${escapeHtml(wifiData.ssid)}</h2>
            </div>
            
            <div class="detail-section">
                <div class="detail-info-item">
                    <label>위험도:</label>
                    <span class="security-level ${wifiData.security_level}">
                        ${getSecurityLevelText(wifiData.security_level)}
                    </span>
                </div>
                <div class="detail-info-item">
                    <label>암호화 여부:</label>
                    <span class="${hasEncryption ? 'encryption-yes' : 'encryption-no'}">${encryptionStatus}</span>
                </div>
            </div>
            
            ${guideInfo && guideInfo.recommendations && guideInfo.recommendations.length > 0 ? `
            <div class="detail-section">
                <h3>권고사항</h3>
                <ul class="detail-recommendations">
                    ${recommendationsList}
                </ul>
            </div>
            ` : ''}
        </div>
    `;
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
