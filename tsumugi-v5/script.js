const cards=[...document.querySelectorAll('.season-card')];
const tabs=[...document.querySelectorAll('.season-nav button')];
const dots=[...document.querySelectorAll('.dots span')];
const carousel=document.querySelector('#seasonCarousel');
let active=1;
let locked=false;
function roleFor(index,activeIndex){const diff=(index-activeIndex+4)%4;return diff===0?'role-main':diff===1?'role-right1':diff===2?'role-right2':'role-left'}
function paintRoles(){cards.forEach((card,i)=>{card.classList.remove('role-main','role-left','role-right1','role-right2');card.classList.add(roleFor(i,active));});tabs.forEach((b,i)=>b.classList.toggle('active',i===active));dots.forEach((d,i)=>d.classList.toggle('active',i===active));}
function go(next,direction=0){if(locked)return;next=(next+4)%4;if(next===active)return;locked=true;const old=active;const dir=direction||(((next-old+4)%4)===1?1:-1);const wrapIndex=dir>0?(old+3)%4:(old+2)%4;cards[wrapIndex].classList.add('wrap');active=next;requestAnimationFrame(()=>paintRoles());setTimeout(()=>cards[wrapIndex].classList.remove('wrap'),430);setTimeout(()=>locked=false,600)}
paintRoles();
tabs.forEach((b,i)=>b.addEventListener('click',()=>{const delta=(i-active+4)%4;go(i,delta===1||delta===2?1:-1)}));
document.querySelector('.prev').addEventListener('click',()=>go(active-1,-1));
document.querySelector('.next').addEventListener('click',()=>go(active+1,1));
let startX=null,startY=null;
carousel.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;startX=e.clientX;startY=e.clientY;carousel.setPointerCapture?.(e.pointerId)});
carousel.addEventListener('pointerup',e=>{if(e.target.closest('button'))return;if(startX===null)return;const dx=e.clientX-startX,dy=e.clientY-startY;startX=startY=null;if(Math.abs(dx)>45&&Math.abs(dx)>Math.abs(dy)*1.2)go(active+(dx<0?1:-1),dx<0?1:-1)});
const drawer=document.querySelector('.drawer'),hamb=document.querySelector('.hamb');
function setDrawer(open){drawer.classList.toggle('open',open);drawer.setAttribute('aria-hidden',String(!open));hamb.setAttribute('aria-expanded',String(open));document.body.style.overflow=open?'hidden':''}
hamb.addEventListener('click',()=>setDrawer(true));document.querySelector('.close').addEventListener('click',()=>setDrawer(false));drawer.addEventListener('click',e=>{if(e.target===drawer)setDrawer(false)});drawer.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>setDrawer(false)));document.addEventListener('keydown',e=>{if(e.key==='Escape')setDrawer(false)});
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('entering');io.unobserve(e.target)}}),{threshold:.08,rootMargin:'40px 0px -30px'});document.querySelectorAll('.reveal').forEach(el=>io.observe(el));