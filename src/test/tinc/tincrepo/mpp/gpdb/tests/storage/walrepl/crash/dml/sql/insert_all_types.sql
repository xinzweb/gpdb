-- start_ignore
SET gp_create_table_random_default_distribution=off;
-- end_ignore
-- Drop table if exists
--start_ignore
DROP TABLE if exists tbl_with_all_type cascade;
--end_ignore

-- Create table
CREATE TABLE tbl_with_all_type 
	(id SERIAL,a1 int,a2 char(5),a3 numeric,a4 boolean DEFAULT false ,a5 char DEFAULT 'd',a6 text,a7 timestamp,a8 character varying(705),a9 bigint,a10 date,a11 varchar(600),a12 text,a13 decimal,a14 real,a15 bigint,a16 int4 ,a17 bytea,a18 timestamp with time zone,a19 timetz,a20 path,a21 box,a22 macaddr,a23 interval,a24 character varying(800),a25 lseg,a26 point,a27 double precision,a28 circle,a29 int4,a30 numeric(8),a31 polygon,a32 date,a33 real,a34 money,a35 cidr,a36 inet,a37 time,a38 text,a39 bit,a40 bit varying(5),a41 smallint,a42 int );

-- Insert data to the table
 INSERT INTO tbl_with_all_type(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23,a24,a25,a26,a27,a28,a29,a30,a31,a32,a33,a34,a35,a36,a37,a38,a39,a40,a41,a42) values(generate_series(1,20),'M',2011,'t','a','This is news of today: Deadlock between Republicans and Democrats over how best to reduce the U.S. deficit, and over what period, has blocked an agreement to allow the raising of the $14.3 trillion debt ceiling','2001-12-24 02:26:11','U.S. House of Representatives Speaker John Boehner, the top Republican in Congress who has put forward a deficit reduction plan to be voted on later on Thursday said he had no control over whether his bill would avert a credit downgrade.',generate_series(2490,2505),'2011-10-11','The Republican-controlled House is tentatively scheduled to vote on Boehner proposal this afternoon at around 6 p.m. EDT (2200 GMT). The main Republican vote counter in the House, Kevin McCarthy, would not say if there were enough votes to pass the bill.','WASHINGTON:House Speaker John Boehner says his plan mixing spending cuts in exchange for raising the nations $14.3 trillion debt limit is not perfect but is as large a step that a divided government can take that is doable and signable by President Barack Obama.The Ohio Republican says the measure is an honest and sincere attempt at compromise and was negotiated with Democrats last weekend and that passing it would end the ongoing debt crisis. The plan blends $900 billion-plus in spending cuts with a companion increase in the nations borrowing cap.','1234.56',323453,generate_series(3452,3462),7845,'0011','2005-07-16 01:51:15+1359','2001-12-13 01:51:15','((1,2),(0,3),(2,1))','((2,3)(4,5))','08:00:2b:01:02:03','1-2','Republicans had been working throughout the day Thursday to lock down support for their plan to raise the nations debt ceiling, even as Senate Democrats vowed to swiftly kill it if passed.','((2,3)(4,5))','(6,7)',11.222,'((4,5),7)',32,3214,'(1,0,2,3)','2010-02-21',43564,'$1,000.00','192.168.1','126.1.3.4','12:30:45','Johnson & Johnsons McNeil Consumer Healthcare announced the voluntary dosage reduction today. Labels will carry new dosing instructions this fall.The company says it will cut the maximum dosage of Regular Strength Tylenol and other acetaminophen-containing products in 2012.Acetaminophen is safe when used as directed, says Edwin Kuffner, MD, McNeil vice president of over-the-counter medical affairs. But, when too much is taken, it can cause liver damage.The action is intended to cut the risk of such accidental overdoses, the company says in a news release.','1','0',12,23); 

 INSERT INTO tbl_with_all_type(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23,a24,a25,a26,a27,a28,a29,a30,a31,a32,a33,a34,a35,a36,a37,a38,a39,a40,a41,a42) values(generate_series(500,510),'F',2010,'f','b','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child','2001-12-25 02:22:11','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child',generate_series(2500,2516),'2011-10-12','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child The type integer is the usual choice, as it offers the best balance between range, storage size, and performance The type integer is the usual choice, as it offers the best balance between range, storage size, and performanceThe type integer is the usual choice, as it offers the best balance between range, storage size, and performanceThe type integer is the usual choice, as it offers the best balance between range, storage size, and performanceThe type integer ','1134.26',311353,generate_series(3982,3992),7885,'0101','2002-02-12 01:31:14+1344','2003-11-14 01:41:15','((1,1),(0,1),(1,1))','((2,1)(1,5))','08:00:2b:01:01:03','1-3','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child The types smallint, integer, and bigint store whole numbers, that is, numbers without fractional components, of various ranges. The types smallint, integer, and bigint store whole numbers, that is, numbers without fractional components, of various ranges. Attempts to store values outside of the allowed range will result in an errorThe types smallint, integer, and bigint store whole numbers, that is, numbers without fractional components, of various ranges.','((6,5)(4,2))','(3,6)',12.233,'((5,4),2)',12,3114,'(1,1,0,3)','2010-03-21',43164,'$1,500.00','192.167.2','126.1.1.1','10:30:55','Parents and other family members are always welcome at Stratford. After the first two weeks ofschool','0','1',33,44); 

 INSERT INTO tbl_with_all_type(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23,a24,a25,a26,a27,a28,a29,a30,a31,a32,a33,a34,a35,a36,a37,a38,a39,a40,a41,a42) values(generate_series(500,525),'M',2010,'f','b','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child','2001-12-25 02:22:11','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child',generate_series(2500,2515),'2011-10-12','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child The bigint type might not function correctly on all platforms, since it relies on compiler support for eight-byte integers.The bigint type might not function correctly on all platforms, since it relies on compiler support for eight-byte integers.The bigint type might not function correctly on all platforms, since it relies on compiler support for eight-byte integers.The bigint type might not function correctly on all platforms, since it relies on compiler support ','1134.26',311353,generate_series(3892,3902),7885,'0101','2002-02-12 01:31:14+1344','2003-11-14 01:41:15','((1,1),(0,1),(1,1))','((2,1)(1,5))','08:00:2b:01:01:03','1-3','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child The type numeric can store numbers with up to 1000 digits of precision and perform calculations exactly. It is especially recommended for storing monetary amounts and other quantities where exactness is required. However, arithmetic on numeric values is very slow compared to the integer types, or to the floating-point types described in the next section.The type numeric can store numbers with up to 1000 digits of precision and perform calculations exactly.','((6,5)(4,2))','(3,6)',12.233,'((5,4),2)',12,3114,'(1,1,0,3)','2010-03-21',43164,'$1,500.00','192.167.2','126.1.1.1','10:30:55','bit type data must match the length n exactly; it is an error to attempt to store shorter or longer','1','10',43,54); 

 INSERT INTO tbl_with_all_type(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23,a24,a25,a26,a27,a28,a29,a30,a31,a32,a33,a34,a35,a36,a37,a38,a39,a40,a41,a42) values(generate_series(600,625),'F',2011,'f','b','If the scale of a value to be stored is greater than the declared scale of the column, the system will round the value to the specified number of fractional digits. Then, if the number of digits to the left of the decimal point ','2001-11-24 02:26:11','bbffruikjjjk89kjhjjdsdsjflsdkfjowikfo;lwejkufhekusgfuyewhfkdhsuyfgjsdbfjhkdshgciuvhdskfhiewyerwhkjehriur687687rt3ughjgd67567tcghjzvcnzfTYr7tugfTRE#$#^%*GGHJFTEW#RUYJBJHCFDGJBJGYrythgfT^&^tjhE655ugHD655uVtyr%^uygUYT&^R%^FJYFHGF',2802,'2011-11-12','Through our sbdfjdsbkfndjkshgifhdsn c  environment, we encourageyour guwr6tojsbdjht8y^W%^GNBMNBHGFE^^, emotional maturity, and a lifetime love of learning.Sign and submit the Stratford enrollment contract and prepaid tuition.Sign and submit the payment authorizahrqwygjashbxuyagsu.','It is very typical for preschool and pre-kindergarten students to experience separation anxietyduring the first few days of school. Please visit the school with your child prior to the first dayof class to help him/her become acquainted with the new environment.As often as possible,speak positively and with encouragement to your child about his/her new school experience.Focus on the excitement and fun of , not the apprehension.It is important to discuss the school procedures with your child. Inform your child that youoom with him','1231.16',121451,4001,2815,'0110','2007-02-12 03:55:15+1317','2011-12-10 11:54:12','((2,2),(1,3),(1,1))','((1,3)(6,5))','07:00:2b:02:01:04','3-2','Some students may need time to adjust to school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the cmnsbvduytfrw67ydwhg uygyth your child','((1,2)(6,7))','(9,1)',12.233,'((2,1),6)',12,1114,'(3,1,2,0)','2011-03-11',22564,'$6,050.00','192.168.2','126.4.4.4','12:31:25','Parents and other family members are always welcome at Stratford. After the first two weeks ofschool, we encourage you to stop by and visit any time you like. When visiting, please berespectful of the classroom environment and do not disturb the students or teachers. Prior toeach visit, we require all visidbsnfuyewfudsc,vsmckposjcofice and obtain a visit sticker to be worn while visiting.As a safety precaution, the Stratford playgrounds are closed for outside visitation during normal school hours. We thank you for your cooperation.','1','1',13,24); 

 INSERT INTO tbl_with_all_type(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23,a24,a25,a26,a27,a28,a29,a30,a31,a32,a33,a34,a35,a36,a37,a38,a39,a40,a41,a42) values(generate_series(1500,1525),'M',2011,'t','b','At Stratford, we believe all children love to learn and that success in school and life depends on developing a strong foundation for learning early in life gsdgdsfoppkhgfshjdgksahdiusahdksahdksahkdhsakdhskahkhasdfu','2001-11-24 02:26:11','ttttttttttttttttrrrrrrrrrrrrrrrrrrrrrtttttttttttttttttttttttttwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwttttttttttttttttttttttttttttttwwwwwwwwwwwwwwwwwwwwweeeeeeeeeeeeeeeeeeeeeeeeeeeeeettttttttttttttttttttttttttttteeeeeeeeeeeeeeeeeeeeeeeeeeedddddddd',2572,'2011-11-12','Through our stimulating dnvuy9efoewlhrf78we68bcmnsbment, we enhsdfiyeowlfdshfkjsdhoifuoeifdhsjvdjnvbhjdfgusftsdbmfnbdstional maturity, and a lifetime loveof learning.Sign and submit the Suythjrbuyhjngy78yuhjkhgvfderujhbdfxrtyuhjcfxdserwhuc  dvfdfofdgjkfrtiomn,eriokljnhbgfdhjkljhgfrtuyhgvform (if required).','It is very typical for preschool and pre-kindergarten students to experience separation anxietyduring the first few days of school. Please visit the school with your child prior to the first dayof class to help him/her become acquainted with the new environment.As often as possible,speak positively and with encouragement to your child about his/her new school experience.Focus on the excitement and fun of school, not the apprehensmnbvcxzasdfghjkoiuytre456789hfghild that you willnot be staying in the classroom with him','1231.16',121451,4001,2815,'0110','2007-02-12 03:55:15+1317','2011-12-10 11:54:12','((2,2),(1,3),(1,1))','((1,3)(6,5))','07:00:2b:02:01:04','3-2','poiuytrewqtgvsxcvbniujhbgvdfrgtyhujjhndcvuhj, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the clasnbdsvuytg uhguyybvhcd with your child','((1,2)(6,7))','(9,1)',12.233,'((2,1),6)',12,1114,'(3,1,2,0)','2011-03-11',22564,'$6,050.00','192.168.2','126.4.4.4','12:31:25','Parents and other family members are always welcome at Stratford. After the first two weeks ofschool, we encourage you to stop b#%J,mbj756HNM&%.jlyyttlnvisiting, please berespectful of the classroom environment and do not disturb the students or teachers. Prior toeach visit, we require all visits to sign in at the school offbduysfifdsna v worn while visiting.As a safety precaution, the Stratford playgrounds are closed for outside visitation during normal school hours. We thank you for your cooperation.','0','1',13,24); 

 INSERT INTO tbl_with_all_type(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23,a24,a25,a26,a27,a28,a29,a30,a31,a32,a33,a34,a35,a36,a37,a38,a39,a40,a41,a42) values(generate_series(3300,3455),'F',2011,'f','b','Numeric values are physically stored without any extra leading or trailing zeroes. Thus, the declared precision and scale of a column are maximums, not fixed allocations jwgrkesfjkdshifhdskjnbfnscgffiupjhvgfdatfdjhav','2002-12-24 02:26:10','uewrtuewfhbdshmmfbbhjjjjjjjjjjjjjjjjjjjjjjjjjewjjjjjjjjjjjjjjsb ffffffffffffffeyyyyyyyyyyyyyyyybcj  hgiusyyyy7777777777eeeeeeeeeeewiuhgsuydte78wt87rwetug7666666we7w86e7w6e87w6ew786ew8e678w6e8w6e8w6e8we6w7e827e6238272377hsys6w6yehsy6wh',2552,'2011-11-12','Through odnviudfygojlskhiusdyfdslfun classroom environment, we encourageyour child to achieve self-confidence, emotional maturity, and a lifetime love of learning.Sign and submit the Stratford enrollment contract and prepaid tuition.Sign and submit the payment authorization form (if required).','It is very typical for presclsjhfdiudhskjfnds,vnc,svljsdaon anxietyduring the first few days of school. Please visimngfrtetyuiujnsbvcrdtr to the first dayof class to help him/her become acquainted with the nsfgsduaytf8fodshkfjhdw786%$%#^&&MBHJFY*IUHjhghgasd76ewhfewagement to your child about his/her new school experience.Focus on the excitement and fun of school, not the apprehension.It is important to discuss the school procedures with yhtyrt$#%^*&*HVGfu8jkGUYT$ujjtygdkfghjklfdhgjkfndkjghfdkgkfdge classroom with him','1231.16',121451,generate_series(5,25),2815,'0110','2007-02-12 03:55:15+1317','2011-12-10 11:54:12','((2,2),(1,3),(1,1))','((1,3)(6,5))','07:00:2b:02:01:04','3-2','Snjhgfytwuie4r893r7yhwdgt678iuhjgfr5678u school.For most children, the adjustment is quick. Tears will usually disappear after Mommy and  Daddy leave the classroom. Do not plead with your child','((1,2)(6,7))','(9,1)',12.233,'((2,1),6)',12,1114,'(3,1,2,0)','2011-03-11',22564,'$6,050.00','192.168.2','126.4.4.4','12:31:25','Parents and other family members are always welcome at Stratford. After the first two weeks ofschool, we encourage you to stop  shasuymnsdjkhsayt6b bnftrrojmbmnctreiujmnb nbfyttojmn, please berespectful of the classroom environment and do not disturb the students or teachers. Prior toeach visit, we require all visitosdfiwe7r09e[wrwdhskcisitors sticker to be worn while visiting.As a safety precaution, the Stratford playgrounds are closed for outside visitation during normal school hours. We thank you for your cooperation.','0','1',13,24); 

 INSERT INTO tbl_with_all_type(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23,a24,a25,a26,a27,a28,a29,a30,a31,a32,a33,a34,a35,a36,a37,a38,a39,a40,a41,a42) values(generate_series(50,55),'M',2011,'f','b','Inexact means that some values cannot be converted exactly to the internal format and are stored as approximations, so that storing and printing back out hwgfrdjwpfidsbhfsyugdskbfkjshfihsdkjfhsjhayiuyihjhvghdhgfjhdva6h','2003-12-24 02:26:11','mjhsiury8w4r9834kfjsdhcjbjghsafre6547698ukljjhgftre4t@%$^&%*&DRTDHGGUY&*^*&(^Gfhe456543^RGHJFYTE%$#!@!~#$%TGJHIU(***$%#@TRFHJG%^$&^*&FHR^%$%UTGHffge45675786gfrtew43ehghjt^%&^86575675tyftyr6tfytr65edf564ttyr565r64tyyyyr4e65tyyyyyyyyyt76',generate_series(700,725),'2011-11-11','Through87678574678uygjr565ghjenvironment, we encourageyour child to achieve ssbfuwet8ryewsjfnjksdhkcmxznbcnsfyetrusdgfdsbhjca lifetime love of learning.Sign and submit the Stratford enrollment contract and prepaid klhgiueffhlskvhfgxtfyuh form (if required).','It is very typical for preschool and pre-kindergarten students to experience separation anxietyduring the first few days of school. Please visit thuytrewfghjkjv cbvnmbvcrte78uhjgnmnbvc5678jnm 4587uijk vacquainted with the new environment.Ajfhgdsufdsjfldsbfcjhgdshhhhhhhhuyhgbn sfsfsdur child about his/her new school experience.Focus on the excitement and fun of school, not the apprehension.It is important to discuss the school procedures with your child. Inform your child that you willnot be stayisdfdsgfuyehfihdfiyiewuyfiuwhfng in the classroom with him','1231.16',121451,4001,2815,'0110','2007-02-12 03:55:15+1317','2011-12-10 11:54:12','((2,2),(1,3),(1,1))','((1,3)(6,5))','07:00:2b:02:01:04','3-2','Some students may need time to adjust to school.jhge7fefvjkehguejfgdkhjkjhgowu09f8r9wugfbwjhvuyTears will usually disappear after Mommy and  Daddy leave the classroom. bdys8snssbss97j with your child','((1,2)(6,7))','(9,1)',12.233,'((2,1),6)',12,1114,'(3,1,2,0)','2011-03-11',22564,'$6,050.00','192.168.2','126.4.4.4','12:31:25','Parents and other family members are always welcome at Stratford. After the first two weeks ofschool, jge7rty3498rtkew mfuhqy970qf wjhg8er7ewrjmwe jhg When visiting, please berespectful of the classroom environment and do not disturb the students or teachers. Prior toeach visit, we require all visits to sign in at the school objjcshgifisdcnskjcbdiso be worn while visiting.As a safety precaution, the Stratford playgrounds are closed for outside visitation during normal school hours. We thank you for your cooperation.','0','1',13,24); 

select count(*) from tbl_with_all_type;
