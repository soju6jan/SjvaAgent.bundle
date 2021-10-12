VERSION = '2021.10.12'

"""
2021.10.12
 - yaml show season 0
 
2021.10.05
 - ftv : 시즌 0도 검색되게
 - lyric URL 생성시에는 key만 넣고, 실제 정보는 메타에서 가져오도록

2021.10.04
 - yaml music 추가
 - yaml dummy agent 추가 : yaml 이외는 다른 처리를 하고 싶지 않을 때

2021.10.01
 - yaml code startswith 체크
 
2021.09.29
 - movie year bug fix
 
2021.09.26
 - JAV DVD로 통합 사용. (검색 실패시 AMA, FC2 순으로 시도)

2021.09.23
 - 기존 jav는 art같은 것이 없는 경우 []를 받았으나 f2c가 추가되면서 null로 리턴하고 있었음.
   필드마다 조건문 추가

2021.09.22
 - 쇼 yaml 파일 처리 추가
 - bug fix

2021.09.15 
 - yaml 라이브러리 포함
 - 영화 yaml 파일 처리 추가

2021.09.07
- jav  xxx-123cd1.json 생성되는 문제 수정

2021.09.02
 - ftv info.json 사용
 
"""