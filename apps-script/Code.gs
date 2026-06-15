/**
 * 台灣舊地圖散策 — 公民科學回報後端 (Google Apps Script Web App)
 * Citizen-science report backend.
 *
 * 收到 App 送來的「位置更正」或「老照片貢獻」後：
 *   · 在試算表 (Google Sheet) 新增一列
 *   · 若有照片，存進指定的 Drive 資料夾，並把連結寫進該列
 *
 * 部署方式見同資料夾的 README.md。
 *
 * App 以 CORS-simple 的 text/plain POST 送出 JSON，因此這裡用
 * e.postData.contents 取得內容。回應一律是 JSON（雖然 App 採
 * no-cors 不讀回應，但保留 JSON 方便用瀏覽器/Postman 手動測試）。
 */

// ── 設定 ──────────────────────────────────────────────
// 留空則自動使用「綁定這支腳本的試算表」的第一個分頁；
// 若用獨立腳本，請填入試算表 ID。
var SHEET_ID = '';
var SHEET_NAME = '回報';        // 分頁名稱（不存在會自動建立）
// 照片要存到的 Drive 資料夾 ID（從資料夾網址 .../folders/<ID> 取得）。
// 留空則自動在雲端硬碟根目錄建立 / 使用「散策回報照片」資料夾。
var PHOTO_FOLDER_ID = '';
var PHOTO_FOLDER_NAME = '散策回報照片';

var HEADERS = [
  '時間', '類型', '明信片ID', '明信片名稱',
  '說明', '建議緯度', '建議經度', '原緯度', '原經度',
  '貢獻者署名', '聯絡方式', '照片連結', '語言', 'UserAgent', '狀態',
];

function doPost(e) {
  try {
    var data = {};
    if (e && e.postData && e.postData.contents) {
      data = JSON.parse(e.postData.contents);
    }
    var sheet = getSheet_();

    var photoUrl = '';
    if (data.type === 'photo' && data.photoDataUrl) {
      photoUrl = savePhoto_(data);
    }

    sheet.appendRow([
      data.ts || new Date().toISOString(),
      data.type || '',
      data.postcardId || '',
      data.postcardTitle || '',
      data.note || '',
      data.suggestedLat != null ? data.suggestedLat : '',
      data.suggestedLng != null ? data.suggestedLng : '',
      data.pinLat != null ? data.pinLat : '',
      data.pinLng != null ? data.pinLng : '',
      data.contributor || '',
      data.contact || '',
      photoUrl,
      data.lang || '',
      data.ua || '',
      '待審核',
    ]);

    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

// 方便用瀏覽器打開測試是否部署成功。
function doGet() {
  return json_({ ok: true, service: 'taiwan-old-map-stroll report endpoint' });
}

function getSheet_() {
  var ss = SHEET_ID
    ? SpreadsheetApp.openById(SHEET_ID)
    : SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    throw new Error('找不到試算表：請設定 SHEET_ID，或把此腳本綁定到一份試算表。');
  }
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function getPhotoFolder_() {
  if (PHOTO_FOLDER_ID) {
    return DriveApp.getFolderById(PHOTO_FOLDER_ID);
  }
  var it = DriveApp.getFoldersByName(PHOTO_FOLDER_NAME);
  return it.hasNext() ? it.next() : DriveApp.createFolder(PHOTO_FOLDER_NAME);
}

function savePhoto_(data) {
  var m = /^data:(image\/[a-zA-Z+]+);base64,(.+)$/.exec(data.photoDataUrl);
  if (!m) return '';
  var contentType = m[1];
  var bytes = Utilities.base64Decode(m[2]);
  var ext = contentType.split('/')[1].replace('jpeg', 'jpg');
  var stamp = (data.ts || new Date().toISOString()).replace(/[:.]/g, '-');
  var name = (data.postcardId || 'photo') + '_' + stamp + '.' + ext;
  var blob = Utilities.newBlob(bytes, contentType, name);
  var file = getPhotoFolder_().createFile(blob);
  // 讓你（擁有者）能直接點開；如需公開可改 ANYONE_WITH_LINK。
  try { file.setSharing(DriveApp.Access.PRIVATE, DriveApp.Permission.VIEW); } catch (e) {}
  return file.getUrl();
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
