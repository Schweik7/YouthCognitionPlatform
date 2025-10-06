% CRT-CC_20 (age range: 5-17)
% import original data from 'CRT_template.xls' 这个文件实际上它只是 id	name	age	score	p	z	iq这一行7个字段
% get percentile, z-score and IQ from CRT_CC_20_norm

dataset = xlsread('CRT_template.xls');   % import original data
norm = xlsread('CRT_CC_20_norm.xls');   % import norm

for i=1:length(dataset(:,1))
    % get original data
    age = dataset(i,1);
    score = dataset(i,2);
    % find the appropriate category
    j=2;
    while age>=(norm(1,j)+0.5)
        j=j+1;
    end
    ageCate = j;
    % find percentile, z-score and iq value
    k=4;
    while score<norm(k,ageCate) && k<18
        k=k+1;
    end
    upper = k;
    if 4<k<18
        while score==norm(k,ageCate) 
            k=k+1;
        end
        lower = k;
        scoreCate = floor(0.5*(upper+lower));
    end
    if k==4
        scoreCate = k-1;
    end
    if k==18
        scoreCate = k+1;
    end
    % export
    dataset(i,3) = norm(scoreCate,1);   % percentile
    dataset(i,4) = norm(scoreCate,14);   % z-score
    dataset(i,5) = norm(scoreCate,15);   % iq
end
    save('dataset');
            
    
    

