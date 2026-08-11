#!/usr/bin/env python3
# CODEX-05 전략 발표 (v3) — 검사기를 정보구조의 중심으로: 라이프사이클 + 7기능표 + 현황표
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

NAVY=RGBColor(0x1F,0x2A,0x44); INK=RGBColor(0x14,0x1B,0x2B); BLUE=RGBColor(0x2E,0x6C,0xB1); TEAL=RGBColor(0x0E,0x8F,0x8F)
AMBER=RGBColor(0xB8,0x79,0x1F); RED=RGBColor(0xB0,0x3A,0x2E); GREEN=RGBColor(0x2E,0x8B,0x57)
GRAY=RGBColor(0x55,0x5B,0x66); WHITE=RGBColor(0xFF,0xFF,0xFF); DARK=RGBColor(0x22,0x27,0x30)
ROW1=RGBColor(0xFF,0xFF,0xFF); ROW2=RGBColor(0xEE,0xF2,0xF7)
KFONT="맑은 고딕"

prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
BLANK=prs.slide_layouts[6]; SW,SH=prs.slide_width,prs.slide_height

def _set(r,s,c,b=False,f=KFONT): r.font.size=Pt(s); r.font.color.rgb=c; r.font.bold=b; r.font.name=f
def box(sl,l,t,w,h):
    tb=sl.shapes.add_textbox(l,t,w,h); tb.text_frame.word_wrap=True; return tb.text_frame
def rect(sl,l,t,w,h,fill):
    sp=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,l,t,w,h); sp.fill.solid(); sp.fill.fore_color.rgb=fill
    sp.line.fill.background(); sp.shadow.inherit=False; return sp
def footer(sl,n):
    tf=box(sl,Inches(0.4),Inches(7.06),Inches(10),Inches(0.33))
    r=tf.paragraphs[0].add_run(); r.text="OpenMetadata 커스텀 버전업 검증 전략 · CODEX-05(정본) 기반"; _set(r,9,GRAY)
    tf2=box(sl,Inches(12.4),Inches(7.06),Inches(0.7),Inches(0.33)); p=tf2.paragraphs[0]; p.alignment=PP_ALIGN.RIGHT
    r=p.add_run(); r.text=str(n); _set(r,9,GRAY)
def head(title,kicker,accent):
    s=prs.slides.add_slide(BLANK)
    rect(s,0,0,SW,Inches(1.15),NAVY); rect(s,0,Inches(1.15),SW,Inches(0.06),accent)
    kf=box(s,Inches(0.5),Inches(0.18),Inches(12.2),Inches(0.35))
    r=kf.paragraphs[0].add_run(); r.text=kicker; _set(r,12,accent,True)
    tf=box(s,Inches(0.5),Inches(0.5),Inches(12.3),Inches(0.62))
    r=tf.paragraphs[0].add_run(); r.text=title; _set(r,25,WHITE,True)
    return s
def content(title,kicker,bullets,accent=BLUE,n=0):
    s=head(title,kicker,accent)
    bf=box(s,Inches(0.6),Inches(1.45),Inches(12.1),Inches(5.4)); first=True
    for it in bullets:
        text,lvl,col=(it if isinstance(it,tuple) else (it,0,DARK))
        p=bf.paragraphs[0] if first else bf.add_paragraph(); first=False
        p.space_after=Pt(6); p.space_before=Pt(2)
        if lvl==0:
            r=p.add_run(); r.text="■ "; _set(r,15,accent,True); r=p.add_run(); r.text=text; _set(r,15,col,True)
        elif lvl==1:
            p.level=1; r=p.add_run(); r.text="– "; _set(r,13,GRAY); r=p.add_run(); r.text=text; _set(r,13,col)
        else:
            p.level=2; r=p.add_run(); r.text="· "+text; _set(r,12,GRAY)
    footer(s,n); return s
def table_slide(title,kicker,headers,rows,widths,accent,n,note=None):
    s=head(title,kicker,accent)
    nrows=len(rows)+1; ncols=len(headers)
    gf=s.shapes.add_table(nrows,ncols,Inches(0.6),Inches(1.5),Inches(12.1),Inches(0.4*nrows))
    tb=gf.table; tb.first_row=False; tb.horz_banding=False
    for j,w in enumerate(widths): tb.columns[j].width=Inches(w)
    for j,h in enumerate(headers):
        c=tb.cell(0,j); c.fill.solid(); c.fill.fore_color.rgb=NAVY
        c.vertical_anchor=MSO_ANCHOR.MIDDLE; c.margin_top=Pt(3); c.margin_bottom=Pt(3)
        p=c.text_frame.paragraphs[0]; r=p.add_run(); r.text=h; _set(r,11,WHITE,True)
    for i,row in enumerate(rows,start=1):
        for j,val in enumerate(row):
            txt,col=(val if isinstance(val,tuple) else (val,DARK))
            c=tb.cell(i,j); c.fill.solid(); c.fill.fore_color.rgb=ROW1 if i%2 else ROW2
            c.vertical_anchor=MSO_ANCHOR.MIDDLE; c.margin_top=Pt(2); c.margin_bottom=Pt(2); c.margin_left=Pt(6)
            p=c.text_frame.paragraphs[0]; p.word_wrap=True; r=p.add_run(); r.text=txt
            _set(r,10.5,col, j==0)
    if note:
        nf=box(s,Inches(0.6),Inches(6.7),Inches(12.1),Inches(0.5))
        r=nf.paragraphs[0].add_run(); r.text=note; _set(r,10,GRAY)
    footer(s,n); return s

# 1 Title
s=prs.slides.add_slide(BLANK); rect(s,0,0,SW,SH,INK); rect(s,0,Inches(4.05),SW,Inches(0.08),TEAL)
tf=box(s,Inches(0.9),Inches(2.0),Inches(11.6),Inches(2.0))
r=tf.paragraphs[0].add_run(); r.text="커스텀 버전업 검증 전략"; _set(r,42,WHITE,True)
p=tf.add_paragraph(); r=p.add_run()
r.text="커스텀 하나가 어떻게 등록되고 · 검사되고 · 증거로 남는가"; _set(r,20,RGBColor(0xBF,0xD3,0xE6))
sf=box(s,Inches(0.9),Inches(4.35),Inches(11.6),Inches(1.6))
for i,t in enumerate(["규칙 기반 자동 검사(단독) → LLM이 일하고 검사기가 근거를 뒷받침",
          "1.13.1 → 1.13.2 예행연습으로 직접 확인 · 정본 CODEX-05 기반","2026-08-10"]):
    p=sf.paragraphs[0] if i==0 else sf.add_paragraph(); r=p.add_run(); r.text=t; _set(r,14,RGBColor(0x9F,0xB2,0xC8))

# 2 배경·목표
content("배경과 처음의 생각","왜 이 일을 시작했나",
 [("목표: 우리가 손댄 부분(DB 커넥터·자체 화면·한글 입력 등)이 공식 버전업 뒤에도 안 깨지고 살아 있는지 확인", 0, DARK),
  ("처음의 전제", 0, DARK),
  ("“AI(LLM)의 판단은 그때그때 달라, 배포 기준으로 삼기엔 믿기 어렵다”", 1, RED),
  ("→ 사람·AI 주관을 빼고, 정해진 규칙(파일 위치·커밋 이력)만 보는 자동 검사로 전부 걸러내자", 1, DARK),
  ("효과: 같은 코드면 항상 같은 결과가 나오는 ‘재현 가능한 자동 판정’", 0, DARK)], BLUE,2)

# 3 초기 구현
content("처음 만든 것 — 규칙 기반 자동 검사기","어떻게 만들었나 (초기)",
 [("파일 위치로 검사: ‘이 기능은 이 파일들에 있어야 한다’를 관리 목록에 적고 대조", 0, DARK),
  ("커밋 이력으로 검사: 커밋마다 ‘무엇을 커스터마이징했는지’ 꼬리표를 달고, 선언 범위 밖을 건드렸는지 확인", 0, DARK),
  ("안전장치: 검사를 못 돌리거나 애매하면 ‘통과’가 아니라 ‘막음’ (= 함부로 초록불이 안 뜬다)", 0, DARK),
  ("못박기: 검사한 코드 상태를 특정 커밋에 못박아, 나중에 슬쩍 바꿔치기 못 하게 한다", 0, DARK)], BLUE,3)

# 4 예행연습
content("예행연습 — 문서가 아니라 실제로","1.13.1 → 1.13.2를 직접",
 [("새 버전(1.13.2) 이미지 빌드 → 기존 데이터 이관 → 서버 기동 → 우리가 만든 API 확인까지 실제로 수행", 0, DARK),
  ("커스텀 기능(InstanceCode)은 실제 서버에서 생성·조회·수정·검색·삭제까지 동작 확인", 0, GREEN),
  ("현재 1.13.2는 ‘부분 확인’ — 일부 화면·데이터 검사가 남아 최종 합격 아님", 0, AMBER),
  ("핵심: 이 예행연습을 하며 ‘무엇이 잘 되고 무엇이 안 되는지’를 몸으로 알게 됐다", 0, DARK)], TEAL,4)

# 5 강점 (정정)
content("예행연습에서 확인한 강점","해보니 이건 확실히 잘 된다",
 [("애매하면 막는다: 검사가 빠지거나 실패하면 자동으로 통과되지 않는다", 0, GREEN),
  ("사람이 판정을 못 뒤집는다: ‘그냥 통과시켜’를 눌러도 위험 판정은 사라지지 않는다", 0, GREEN),
  ("결과 변경 감지: 저장된 판정이 바뀌면 ‘내용 지문’이 어긋나 티가 난다 (전자서명·외부공증은 아님)", 0, GREEN),
  ("‘속 빈 테스트’ 색출: 기능을 일부러 빼봤을 때 그 테스트가 실패해야 진짜로 인정", 0, GREEN),
  ("1.13.1은 필수 Contract 9개를 전부 통과", 0, GREEN),
  ("정확히는 API 4 · 브라우저(화면) 3 · 소스 정합성 2 = 9 — 9개 전부가 ‘서버 동작’ 검사는 아니다", 1, DARK)], GREEN,5)

# 6 한계1
content("그런데 ① 운영이 힘들다 — 관리 파일이 너무 많다","해보니 드러난 한계",
 [("무엇을 바꿨는지·어디까지 허용인지·누가 승인했는지를 전부 사람이 파일로 관리", 0, RED),
  ("버전업 때마다 이 목록들을 일일이 갱신해야 한다", 1, DARK),
  ("→ ‘검사 자체’보다 ‘검사를 유지하는 비용’이 더 크다 (지속 운영의 벽)", 1, DARK),
  ("목록이 늘수록 갱신 누락·중복 검사·피로로 인한 형식적 승인 위험이 커진다", 1, DARK)], RED,6)

# 7 한계2
content("그리고 ② 규칙 검사만으로는 못 보는 것들","해보니 드러난 한계",
 [("공식이 코드를 다른 파일로 옮기면 못 따라간다 (가장 큰 약점)", 0, RED),
  ("옛 위치만 보고 “사라졌다”고 오판 — 실제로 Sybase·Tibero 커넥터에서 오탐 발생", 1, AMBER),
  ("“파일이 공식과 다르다” ≠ “기능이 온전하다” — 반쯤 깨져도 ‘다르기만’ 하면 통과 가능", 0, RED),
  ("승인자가 진짜 권한자인지, 충돌이 실제로 얼마나 났는지는 사람이 적어넣는 값이라 검증 못 함", 0, RED),
  ("→ 규칙(파일·글자 기준)을 더 붙여도 이 약점은 반복된다 (구조적 한계)", 0, DARK)], RED,7)

# 8 8/5 검토
content("8/5 공유된 ‘LLM 기반 운영 방식’을 함께 검토","다른 접근에서 얻은 힌트",
 [("강점: 규칙·지식 문서·자동화로 버전 포팅 시간을 크게 줄였다 (빠르고 체계적)", 0, GREEN),
  ("구조: 변경·수정·테스트·결과 기록을 대부분 LLM이 스스로 수행하고 결과도 스스로 문서에 적는다", 0, DARK),
  ("검토 소감 (까려는 게 아니라 보완 제안)", 0, BLUE),
  ("여기에 검사기로 ‘각 판단의 근거를 자동으로 뒷받침’하는 층을 더하면, 속도는 살리고 신뢰는 올릴 수 있겠더라", 1, BLUE),
  ("두 방식은 경쟁이 아니라 ‘빠른 실행 + 단단한 근거’로 합쳐진다", 1, DARK)], BLUE,8)

# 9 방향
content("그래서 방향 — LLM이 일하고, 검사기가 근거를 붙인다","방향 전환",
 [("LLM = 판단·제안: 무엇을 바꿀지, 코드가 어디로 옮겨졌을지, 충돌 해결, 필요한 테스트", 0, BLUE),
  ("검사기 = 뒷받침: 그 판단을 실제 코드·실행 증거로 확인하고, 위험하면 막는다", 0, TEAL),
  ("핵심 규칙", 0, DARK),
  ("LLM이 ‘됐다(✅)’고 적어도, 실제 코드·실행 증거가 없으면 ‘미확인’으로 표시한다", 1, RED),
  ("증거 없다고 곧장 ‘거짓’으로 몰지 않는다 → 확인 / 반박 / 미확인 / 사람검토 4단계", 1, DARK)], BLUE,9)

# 10 라이프사이클 (핵심)
content("커스텀 하나(BANK-OM ID)가 검증되는 과정","도입 제안 — LLM 작업의 ‘증거 층’으로 이 검사기를 도입(자랑 아님)",
 [("제안: 하이브리드에서 LLM 판단의 증거 층으로 이 시스템을 도입한다. 커스텀 하나가 아래 6단계로 등록·검사·증거화된다.", 0, DARK),
  ("① 등록 — Manifest·Registry·Contract에 올린다", 0, TEAL),
  ("무엇을·어디를 바꿨고, 어떤 전용 계약으로 지킬지 선언", 1, DARK),
  ("② 커밋·변경범위 검사", 0, TEAL),
  ("이 ID가 선언한 범위만 건드렸는지, 공식 계보 위에 얹혔는지 확인", 1, DARK),
  ("③ 공용 파일의 ID별 코드 검사", 0, TEAL),
  ("여러 기능이 공유하는 파일에서 이 ID 몫의 코드가 살아있고 공식과 달라졌는지", 1, DARK),
  ("④ 전용 Contract 실행", 0, TEAL),
  ("이 기능만의 계약 테스트를 돌린다 (API / 화면 / 소스) — 속 빈 테스트면 patch-kill로 걸러냄", 1, DARK),
  ("⑤ commit·이미지와 결과 결속", 0, TEAL),
  ("검사 결과를 특정 커밋·이미지에 못박아 바꿔치기·사후수정을 탐지", 1, DARK),
  ("⑥ 승인·증거 보관", 0, TEAL),
  ("권한자 승인 + 증거(무엇을·어떤 코드에서·어떤 결과) 보관 — 승인은 결과에 결속", 1, DARK)], TEAL,10)

# 11 7기능표
table_slide("7개 기능별 Contract 검사표 (BANK-OM-001~007)","기능마다 전용 계약이 할당된다",
 ["ID","기능","계약 유형","중요도","현재 검증 상태"],
 [["001","InstanceCode","API","high",("1.13.1 통과 · 1.13.2 실제 동작 통과",GREEN)],
  ["002","QueryReport","API","high",("1.13.1 통과 · 1.13.2 부분(픽스처 필요)",AMBER)],
  ["003","Data Assertions","API + 화면","high",("API 통과 · 화면 별도 도구로 확인",AMBER)],
  ["004","은행 컬럼 확장 표시","API + 화면","medium",("API 통과 · 화면 통과(도구)",GREEN)],
  ["005","한글 IME 보정","화면","medium",("도구 지원 확인됨 · 경로 확보 후 실행",AMBER)],
  ["006","Sybase 커넥터","소스 정합성","high",("1.13.1 통과 · patch-kill 입증 · 1.13.2 코드이동→재anchor",AMBER)],
  ["007","Tibero 커넥터","소스 정합성","high",("1.13.1 통과 · patch-kill 입증 · 1.13.2 코드이동→재anchor",AMBER)]],
 [0.8,3.0,1.9,1.2,5.2], TEAL,11,
 note="필수 Contract 9개 = 위 required_test 합(API 4 · 화면 3 · 소스 2). 008~011은 기술 보완용 임시 ID(InstanceCode·QueryReport 계약에 연결, 사용자 확정 전).")

# 12 현황표
table_slide("정직한 검증 현황","무엇이 어디까지 됐나 — 과장 없이",
 ["항목","현황"],
 [["1.13.1 필수 Contract",("9/9 통과 (API 4 · 화면 3 · 소스 정합성 2)",GREEN)],
  ["Patch-kill (속 빈 테스트 방지)",("Sybase·Tibero 소스 제거 실험 입증 완료 / 나머지 Runtime 제거 실험은 미완료",AMBER)],
  ["1.13.2 업그레이드",("InstanceCode 실제 동작 통과 / 나머지는 부분 검증",AMBER)],
  ["주장–증거 자동 대조기",("향후 설계 (미구현)",GRAY)]],
 [3.2,8.9], NAVY,12)

# 13 MD vs 검사기 (정정)
s=head("왜 ‘MD 문서’가 아니라 ‘검사기’인가","원리 — 대표 예시 4개 (전부가 아님)",TEAL)
bf=box(s,Inches(0.6),Inches(1.4),Inches(12.1),Inches(1.05))
p=bf.paragraphs[0]; r=p.add_run()
r.text="‘도움’은 아래 4개가 아니다 — 앞의 6단계 × 7개 전용 계약 전부가 LLM의 각 주장에 증거를 붙인다. 아래는 그 원리의 대표 예시다. "
_set(r,12.5,DARK,True)
r=p.add_run(); r.text="문서는 스스로 적는 글이라 안 해보고/고쳐도 티가 안 나지만, 검사기 증거는 지어내기 어렵고 보호된 CI에서 생성·보관하면 임의 변경을 탐지할 수 있다."
_set(r,12.5,DARK)
table_rows=[["“이 파일 바꿨다”","말만 믿게 됨","실제 커밋 변경을 직접 대조"],
 ["“충돌 0건”","안 해봐도 적힘","임시로 실제 병합해 충돌 수를 센다"],
 ["“테스트 통과”","적으면 끝","실제 서버에서 재실행, 미실행=통과 아님"],
 ["“승인함”","아무 이름이나","승인을 결과에 묶어 입력 바뀌면 무효"]]
gf=s.shapes.add_table(len(table_rows)+1,3,Inches(0.6),Inches(2.5),Inches(12.1),Inches(3.0)); tb=gf.table
tb.first_row=False; tb.horz_banding=False
for j,w in enumerate([3.0,3.9,5.2]): tb.columns[j].width=Inches(w)
for j,h in enumerate(["LLM의 주장","문서(MD)만: 위험","검사기가 하는 것"]):
    c=tb.cell(0,j); c.fill.solid(); c.fill.fore_color.rgb=NAVY; c.margin_left=Pt(6)
    r=c.text_frame.paragraphs[0].add_run(); r.text=h; _set(r,11,WHITE,True)
for i,row in enumerate(table_rows,start=1):
    cols=[DARK,RED,GREEN]
    for j,val in enumerate(row):
        c=tb.cell(i,j); c.fill.solid(); c.fill.fore_color.rgb=ROW1 if i%2 else ROW2; c.margin_left=Pt(6)
        r=c.text_frame.paragraphs[0].add_run(); r.text=val; _set(r,11,cols[j], j==0)
cf=box(s,Inches(0.6),Inches(5.9),Inches(12.1),Inches(0.8))
r=cf.paragraphs[0].add_run()
r.text="한 줄: 검사기는 ‘LLM이 실제로 일했다는 증거’를 만든다 — 보호된 CI에서 만들고 보관하면 임의 변경이 탐지된다."
_set(r,13,GREEN,True)
footer(s,13)

# 14 독립성·역할
content("지켜야 할 조건 & 검사기의 정확한 위치","오해 방지",
 [("LLM이 실행·기록·증거·승인을 다 하면 그건 ‘독립 검증’이 아니다", 0, RED),
  ("별도의 보호된 자동화(CI)가 실제 코드를 받아 검사를 돌려야 한다 — LLM은 요약만, 판정은 못 바꾼다", 1, DARK),
  ("검사기 초록불 = “코드·기록·증거가 앞뒤 맞다” — “모든 기능 정상·배포 안전”까지는 아니다", 0, DARK),
  ("최종 배포에 필요한 4가지", 0, GREEN),
  ("①변경 범위 정합성 ②검사한 코드=배포할 코드 ③실제 서버 동작 검사 ④권한 있는 사람 승인", 1, DARK)], NAVY,14)

# 15 결론
content("결론","한 장 요약",
 [("규칙 검사: 강력한 ‘근거·통제 장치’지만 혼자선 운영 부담 + 못 보는 맹점", 0, DARK),
  ("LLM 운영: 빠르지만 스스로 적은 기록이라 근거가 약하다", 0, DARK),
  ("답 = LLM이 빠르게 일하고, 검사기가 그 근거를 (보호된 CI에서) 뒷받침하는 결합", 0, GREEN),
  ("커스텀 하나하나가 등록→범위검사→ID별 코드검사→전용 Contract→결속→승인·증거로 흐른다", 0, TEAL),
  ("현재: 1.13.1 필수 Contract 9/9 · 1.13.2 부분 검증 / 다음: 주장–증거 자동 대조기 설계", 0, DARK)], GREEN,15)

out="/Users/seop/openmetadata-lab/docs/CODEX-05-전략발표.pptx"
prs.save(out); print("saved:",out,"| slides:",len(prs.slides._sldIdLst))
