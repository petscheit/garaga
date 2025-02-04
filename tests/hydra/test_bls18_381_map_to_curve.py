from garaga.modulo_circuit import WriteOps
from garaga.precompiled_circuits.map_to_curve import MapToCurveG1, MapToCurveG2


def test_bls18_381_map_to_curve_g2_non_quadratic():
    circuit = MapToCurveG2("test", 1)
    circuit.set_consts()

    field = circuit.write_elements(
        [
            circuit.field(
                3741944764571472160006322193608041966151877622471123223277469611910821820061028054244113212685535996904839352799402
            ),
            circuit.field(
                2076377621229436486953902801269393160218977179950230047408992877427440885760409779221205731516804245080380194857867
            ),
        ],
        WriteOps.INPUT,
    )

    g1x, div, num_x1, zeta_u2 = circuit.map_to_curve_part_1(field)

    # Assert intermediate results
    assert (
        g1x[0].emulated_felt.value
        == 953996773580150187658453355749387256203585747550541475689949001565592017941792784008487857020741875161940439358169
    )
    assert (
        g1x[1].emulated_felt.value
        == 1091041959624877033265075916985653082630429384881674462548287154185532968300913190673468388150241943339667076518253
    )

    assert (
        div[0].emulated_felt.value
        == 1271124738425673168909051490409346544806999942963856749219399676853245141674638476952210593612982147617933716830990
    )
    assert (
        div[1].emulated_felt.value
        == 2707549614030537572533166896762785147996244686855330285575235995466755739337470183080976608052299087222211278178288
    )

    assert (
        num_x1[0].emulated_felt.value
        == 3368717908425370587121521256961562283349295337955434359453978866874955592536159067888255032927442968748123109596151
    )
    assert (
        num_x1[1].emulated_felt.value
        == 3415444388557434595807082624117973727069974003779938583652094445339905219350042585004730694719550642891646061378068
    )

    assert (
        zeta_u2[0].emulated_felt.value
        == 2066503771099735372725208757434934470387642893685367231392552060087408173898621033802030119021772665098131312925308
    )
    assert (
        zeta_u2[1].emulated_felt.value
        == 1011496392125783422068061997226415746244229915320831072846626167000664891392171563621675612638222437312051389941143
    )

    (x_affine, y) = circuit.finalize_map_to_curve_non_quadratic(
        field, g1x, div, num_x1, zeta_u2
    )

    # Assert final results
    assert (
        x_affine[0].emulated_felt.value
        == 2006413752686223508612366075043722458232321744863932880413784802489452766740742045984482044248764924205010366531647
    )
    assert (
        x_affine[1].emulated_felt.value
        == 2103918733930157635900741069076788853417130098910518594897125230089087553459780427160470339353748226243766968776215
    )

    assert (
        y[0].emulated_felt.value
        == 2345181275451808874246097791768578660839971403546046193253448677984295781774410213317345275973043584946083029690838
    )
    assert (
        y[1].emulated_felt.value
        == 491718355885353185704655750809656447183587281146662745649897882009019112506313662303269809992594062560315039747134
    )


def test_bls18_381_map_to_curve_g2_quadratic():
    circuit = MapToCurveG2("test", 1)
    circuit.set_consts()

    field = circuit.write_elements(
        [
            circuit.field(
                1556800727266659224486307223710983989761661593776178353933175239605467918853638579207638742450628877266610077644019
            ),
            circuit.field(
                2231413721970278425038638834062370180699174210864795385441649994565282274875534254514118105433862522641883533654145
            ),
        ],
        WriteOps.INPUT,
    )

    g1x, div, num_x1, zeta_u2 = circuit.map_to_curve_part_1(field)

    # Assert intermediate results
    assert (
        g1x[0].emulated_felt.value
        == 1741461048819108320601120926297383578798673393844727619465122674954412335152552581570073244593349691385858884173583
    )
    assert (
        g1x[1].emulated_felt.value
        == 622728400870450638897257156989331087788861565586056105959821305999301052577755232615332472975146795773248285518397
    )

    assert (
        div[0].emulated_felt.value
        == 245484112468371472016059514225945212312552892410862615098545961349697995155733061412689120985823985643121008707443
    )
    assert (
        div[1].emulated_felt.value
        == 2710033076136311888860218740720521072952923210029411465485968205608170799418483286817121694092479356648635501832540
    )

    assert (
        num_x1[0].emulated_felt.value
        == 678813894361393103360103286141952477825674360176586850375556142934890501990305386551122112060089003594179575462051
    )
    assert (
        num_x1[1].emulated_felt.value
        == 481031161552380994425457621530411412945970154876090436018460806513725659192179414613944042534095739563026661110941
    )

    assert (
        zeta_u2[0].emulated_felt.value
        == 2605347211487192472869035898066121846694525878433542755302801455037350149869786867270039608133704248908541829065188
    )
    assert (
        zeta_u2[1].emulated_felt.value
        == 2186733141282187687524429079326838649285331456588145172920951615849025076744838489106511432055390831654029460361575
    )

    (x_affine, y) = circuit.finalize_map_to_curve_quadratic(field, g1x, div, num_x1)

    # Assert final results
    assert (
        x_affine[0].emulated_felt.value
        == 2843075373688611471290556504186176053275483247291128525980163517764803526616259371130035811825227707920936817728741
    )
    assert (
        x_affine[1].emulated_felt.value
        == 3661712616179456093275454398202160102594067191736010383603184812959944211042529505618295008186663134429283699505891
    )

    assert (
        y[0].emulated_felt.value
        == 2229899020770589661585214900480830515873415727829711460134445858387853696109925143060238999266818473086058450471795
    )
    assert (
        y[1].emulated_felt.value
        == 3127664777588830509127251096086955764006894160737524705993294599144750103128110100147816255502757346871240956727581
    )


def test_bls18_381_map_to_curve_g1_quadratic():
    circuit = MapToCurveG1("test", 1)
    circuit.set_consts()

    field = circuit.write_element(
        circuit.field(
            2231413721970278425038638834062370180699174210864795385441649994565282274875534254514118105433862522641883533654145
        )
    )

    g1x, div, num_x1, zeta_u2 = circuit.map_to_curve_part_1(field)

    # Assert intermediate results
    assert (
        g1x.emulated_felt.value
        == 2597611908074869266676097344052780591254059561619989704088799034359084350987704445977946845985385140941235233170571
    )
    assert (
        div.emulated_felt.value
        == 2805237479025562283149334731040192757369528037210657601602127558394884972035943561694397352660127862349210615463142
    )
    assert (
        num_x1.emulated_felt.value
        == 357516532893183420527219030989999274866612035539674613298479245292141662614414253856542640697610990033784993055353
    )
    assert (
        zeta_u2.emulated_felt.value
        == 1458720157247399937074920312179320190319011370446888399995409372377477911247349655187476411795089883075347478260790
    )

    (x_affine, y_initial, field) = circuit.compute_initial_coordinates_quadratic(
        field, g1x, div, num_x1
    )

    (y_affine, qy, qfield) = circuit.adjust_y_sign(field, y_initial)

    # Assert final results
    assert (
        x_affine.emulated_felt.value
        == 821680820282835312240647697969669528662337868557420531415876216710180320418897646214379495222032594074174798424202
    )
    assert (
        y_affine.emulated_felt.value
        == 2810929796268343801118836101228108033947242316820103062127644703467142871560955216144508646104360230898984292110363
    )


def test_bls18_381_map_to_curve_g1_non_quadratic():
    circuit = MapToCurveG1("test", 1)
    circuit.set_consts()

    field = circuit.write_element(
        circuit.field(
            1556800727266659224486307223710983989761661593776178353933175239605467918853638579207638742450628877266610077644019
        )
    )

    g1x, div, num_x1, zeta_u2 = circuit.map_to_curve_part_1(field)

    # Assert intermediate results
    assert (
        g1x.emulated_felt.value
        == 341972610627912974245460429393853020244324285563375868527372516439156668443097006714852415949547549919046535667616
    )
    assert (
        div.emulated_felt.value
        == 437377489188823988571636230286582387258102034988413032009071756963827842481400269867189494736241034037731549310834
    )
    assert (
        num_x1.emulated_felt.value
        == 859079108276904279242178106413495842276094320054147243681841678369946208284556898300157013329362279916993343726889
    )
    assert (
        zeta_u2.emulated_felt.value
        == 3595463469902610153619251584554498156597029272564817168764456841515827675239496939601340079478403412813212271353518
    )

    (x_affine, y_initial, field) = circuit.compute_initial_coordinates_non_quadratic(
        field, g1x, div, num_x1, zeta_u2
    )

    (y_affine, qy, qfield) = circuit.adjust_y_sign(field, y_initial)

    # Assert final results
    assert (
        x_affine.emulated_felt.value
        == 1412853964218444964438936699552956047210482383152224645596624291427056376487356261681298103080878386132407858666637
    )
    assert (
        y_affine.emulated_felt.value
        == 752734926215712395741522221355891264404138695398702662135908094550118515106801651502315795564392519475687558113863
    )
